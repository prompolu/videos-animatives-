const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {execFileSync} = require('node:child_process');
const root = __dirname, folder = path.join(root,'assets/audio');
fs.mkdirSync(folder,{recursive:true});
const cues = [];
function cue(effect,time,gain=.22,duration=.5,trim=0,peak=true){cues.push({effect,time,gain,duration,trim,align_peak:peak})}
cue('riser',0,.14,1.2,8.8,false);
cue('whoosh',1.2,.32,.57);
for(let i=0;i<8;i++)cue('key-press',3.7+i*.2,.11,.16);
cue('click',6.8,.27,.25);
cue('click-soft',8.76,.2,.25);
for(let i=0;i<8;i++)cue('key-press',9.2+i*.1,.075,.12);
cue('click',10.2,.27,.25);
[11,11.3,11.6].forEach(t=>cue('pop',t,.22,.45));
[12.2,12.9,13.6].forEach(t=>cue('ping',t,.12,.38));
[14.3,14.8,15.3].forEach(t=>cue('notification',t,.17,.7));
cue('whoosh-short',16.9,.24,.57);cue('chime',16.9,.14,.85);
cue('whoosh-short',17.4,.3,.57);cue('whoosh',17.9,.33,.57);
cue('impact-bass-1',18.6,.32,1.1);cue('sparkle',19,.16,1.0);
const peaks={},samples={};
for(const effect of new Set(cues.map(c=>c.effect))){
 const file=path.join(root,'assets/sfx',effect+'.mp3');
 const raw=execFileSync('ffmpeg',['-v','error','-i',file,'-ac','1','-ar','48000','-f','f32le','pipe:1'],{maxBuffer:8e6});
 const values=new Float32Array(raw.buffer,raw.byteOffset,Math.floor(raw.length/4));
 samples[effect]=values;
 let peak=0,index=0;
 for(let i=0;i<values.length;i+=240){let sum=0;for(let j=i;j<Math.min(values.length,i+240);j++)sum+=values[j]*values[j];if(sum>peak){peak=sum;index=i}}
 peaks[effect]=index/48000;
}
const args=['-hide_banner','-loglevel','error','-y','-filter_complex_threads','1'];
for(const c of cues)args.push('-i',path.join(root,'assets/sfx',c.effect+'.mp3'));
const filters=cues.map((c,i)=>{
 const values=samples[c.effect];
 const begin=Math.floor(c.trim*48000),end=Math.min(values.length,Math.floor((c.trim+c.duration)*48000));
 let energy=-1,position=begin;
 for(let p=begin;p<end;p+=240){let sum=0;for(let q=p;q<Math.min(end,p+240);q++)sum+=values[q]*values[q];if(sum>energy){energy=sum;position=p}}
 const inside=Math.min(c.duration-.005,Math.max(.005,(position-begin+120)/48000));
 c.start=Math.max(0,c.align_peak?c.time-inside:c.time);
 c.measured_full_source_peak=peaks[c.effect];c.measured_used_clip_peak=inside;c.scheduled_peak=c.start+inside;
 return `[${i}:a]atrim=start=${c.trim}:duration=${c.duration},asetpts=PTS-STARTPTS,aresample=48000,afade=t=in:st=0:d=0.005,afade=t=out:st=${Math.max(0,c.duration-.04)}:d=0.04,volume=${c.gain},adelay=${Math.round(c.start*1000)}:all=1[c${i}]`;
});
filters.push(cues.map((_,i)=>`[c${i}]`).join('')+`amix=inputs=${cues.length}:normalize=0,apad,atrim=duration=20,afade=t=in:st=0:d=0.01,afade=t=out:st=19.85:d=0.15[mix]`);
const temp=path.join(fs.mkdtempSync(path.join(os.tmpdir(),'promark-audio-')),'raw.wav');
args.push('-filter_complex',filters.join(';'),'-map','[mix]','-ac','2','-ar','48000','-c:a','pcm_s24le',temp);
execFileSync('ffmpeg',args);
const analysis=require('node:child_process').spawnSync('ffmpeg',['-hide_banner','-i',temp,'-af','loudnorm=I=-18:TP=-1:LRA=9:print_format=json','-f','null','-'],{encoding:'utf8'});
if(analysis.status!==0)throw Error(analysis.stderr);
const found=analysis.stderr.match(/\{\s*"input_i"[\s\S]*?\}/);if(!found)throw Error('No loudness measurements');
const measured=JSON.parse(found[0]);
execFileSync('ffmpeg',['-v','error','-y','-i',temp,'-af',`loudnorm=I=-18:TP=-1:LRA=9:measured_I=${measured.input_i}:measured_TP=${measured.input_tp}:measured_LRA=${measured.input_lra}:measured_thresh=${measured.input_thresh}:offset=${measured.target_offset}:linear=true`,'-ar','48000','-ac','2','-c:a','pcm_s24le',path.join(folder,'sfx-master.wav')]);
fs.writeFileSync(path.join(folder,'cues.json'),JSON.stringify({duration:20,source:'HyperFrames bundled sound library; original recordings retained; no synthesized SFX',voice:'Deferred by user; no voice track or false transcription',music:'None; to add in-app or from client track',peak_analysis_window_ms:5,cues,loudness_input:measured},null,2)+'\n');
fs.writeFileSync(path.join(root,'voice-cues.json'),JSON.stringify({status:'voice deferred by user',voice_requested:'Vivienne, French, female',timings:'User-requested cue starts, not measured speech timings',cues:[{start:2.6,text:'Vos clients vous cherchent déjà…'},{start:6.4,text:'…encore faut-il qu’ils vous trouvent.'},{start:9.2,text:'Contenus, réseaux sociaux, sites web : Promark fait parler de votre marque.'},{start:12.6,text:'Et les demandes arrivent.'},{start:17.8,text:'Promark. Pour les entreprises qui veulent être vues.'}]},null,2)+'\n');
fs.rmSync(path.dirname(temp),{recursive:true});
console.log(`Mixed ${cues.length} sound cues. Stereo, 48 kHz, 20 seconds; no music or voice.`);
