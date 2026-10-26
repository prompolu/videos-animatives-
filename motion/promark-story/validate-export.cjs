const fs=require('node:fs');const path=require('node:path');
const {execFileSync,spawnSync}=require('node:child_process');const crypto=require('node:crypto');
const {chromium}=require('playwright');
const root=__dirname;const file=path.join(root,'renders/promark-story-sfx.mp4');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const probe=JSON.parse(execFileSync('ffprobe',['-v','error','-count_frames','-show_streams','-show_format','-of','json',file],{encoding:'utf8'}));
 const v=probe.streams.find(s=>s.codec_type==='video'),a=probe.streams.find(s=>s.codec_type==='audio');
 if(!v||v.width!==1080||v.height!==1920||v.avg_frame_rate!=='30/1'||Number(v.nb_read_frames)!==600||Math.abs(Number(probe.format.duration)-20)>.04)throw Error('Wrong video dimensions, fps, frame count or duration');
 if(!a||a.codec_name!=='aac')throw Error('Expected AAC sound-effects track');
 execFileSync('ffmpeg',['-xerror','-v','error','-i',file,'-f','null','-']);
 const ends=execFileSync('ffmpeg',['-v','error','-i',file,'-vf',"select='eq(n,0)+eq(n,599)'",'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],{maxBuffer:15e6});
 const size=1080*1920*3;if(ends.length!==size*2)throw Error('Loop frame extraction failed');
 let difference=0,max=0;for(let i=0;i<size;i++){const d=Math.abs(ends[i]-ends[i+size]);difference+=d;max=Math.max(max,d)}
 const mean=difference/size;if(mean>1)throw Error('Loop endpoints differ materially: '+mean);
 const metering=spawnSync('ffmpeg',['-hide_banner','-i',file,'-af','loudnorm=I=-18:TP=-1:LRA=9:print_format=json','-f','null','-'],{encoding:'utf8'});
 if(metering.status!==0)throw Error(metering.stderr);
 const match=metering.stderr.match(/\{\s*"input_i"[\s\S]*?\}/);if(!match)throw Error('Loudness measurement absent');
 const loudness=JSON.parse(match[0]);if(Number(loudness.input_tp)>-.1)throw Error('Insufficient true-peak headroom');
 const raw=execFileSync('ffmpeg',['-v','error','-i',file,'-vf','scale=96:170','-f','rawvideo','-pix_fmt','gray','pipe:1'],{maxBuffer:12e6});
 const pixels=96*170;if(raw.length!==600*pixels)throw Error('Motion analysis did not decode all 600 frames');
 const deltas=[];for(let n=1;n<600;n++){let s=0;for(let p=0;p<pixels;p++)s+=Math.abs(raw[n*pixels+p]-raw[(n-1)*pixels+p]);deltas.push({frame:n,time:n/30,mean:s/pixels})}
 const peaks=[...deltas].sort((x,y)=>y.mean-x.mean).slice(0,12);
 const video=fs.readFileSync(file);
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox'],env:{...process.env,XDG_CACHE_HOME:'/tmp/promark-browser-cache',XDG_CONFIG_HOME:'/tmp/promark-browser-config'}});
 try{const page=await browser.newPage();await page.setContent(`<video id="v" controls muted playsinline src="data:video/mp4;base64,${video.toString('base64')}"></video>`);
  await page.evaluate(async()=>{const v=document.getElementById('v');await v.play()});
  await page.waitForFunction(()=>document.getElementById('v').ended,null,{timeout:35000});
 }finally{await browser.close()}
 const report={status:'passed',file:path.basename(file),sha256:sha(video),duration:Number(probe.format.duration),width:v.width,height:v.height,fps:30,frames:Number(v.nb_read_frames),video_codec:v.codec_name,audio_codec:a.codec_name,audio_sample_rate:a.sample_rate,full_decode:'passed',browser_playback_to_end:'passed',loop:{first_last_frame_mean_absolute_rgb_difference:mean,max_rgb_difference:max,tolerance_mean_rgb_levels:1},audio:{integrated_lufs:Number(loudness.input_i),true_peak_dbtp:Number(loudness.input_tp),music:false,voice:false,voice_status:'Deferred at user request'},motion_analysis:{frames:600,consecutive_pairs:599,largest_peaks:peaks},source_index_sha256:sha(fs.readFileSync(path.join(root,'index.html'))),notes:['Stylized social interface: counters and messages follow the requested storyboard, not live account statistics','Website plates captured from the repository bundled site; direct GitHub Pages request was denied','Short reading times and transition overlaps are reviewed against the explicit client timing']};
 fs.writeFileSync(path.join(root,'renders/validation.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({frames:report.frames,duration:report.duration,loopMean:mean,lufs:report.audio.integrated_lufs,truePeak:report.audio.true_peak_dbtp,playback:'passed'},null,2));
})().catch(e=>{console.error(e);process.exit(1)});
