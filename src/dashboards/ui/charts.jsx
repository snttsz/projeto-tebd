import React,{useId,useState,useRef,useLayoutEffect} from 'react';
import {createPortal} from 'react-dom';
import {fmt,num,sum,months} from './model.mjs';

function useChartTooltip(){
  const [tip,setTip]=useState(null);
  const show=(e,title,entries)=>{const r=e.currentTarget.getBoundingClientRect?.();setTip({title,entries,
    x:Number.isFinite(e.clientX)?e.clientX:(r?.left||0)+(r?.width||0)/2,
    y:Number.isFinite(e.clientY)?e.clientY:(r?.top||0)+(r?.height||0)/2})};
  return {tip,show,hide:()=>setTip(null)};
}

function ChartTooltip({tip}){
  const ref=useRef(null),[position,setPosition]=useState({left:0,top:0});
  useLayoutEffect(()=>{
    if(!tip)return;
    const rect=ref.current?.getBoundingClientRect?.(),width=rect?.width||280,height=rect?.height||120;
    const viewportWidth=window.innerWidth||1024,viewportHeight=window.innerHeight||768;
    let left=tip.x+16,top=tip.y+16;
    if(left+width>viewportWidth-12)left=tip.x-width-16;
    if(top+height>viewportHeight-12)top=tip.y-height-16;
    setPosition({left:Math.max(12,Math.min(left,viewportWidth-width-12)),top:Math.max(12,Math.min(top,viewportHeight-height-12))});
  },[tip]);
  if(!tip)return null;
  return createPortal(<div ref={ref} role="tooltip" className="chart-tooltip" style={position}><strong>{tip.title}</strong>{tip.entries.map((entry,i)=><div key={i}><span>{entry.color&&<i className="dot" style={{background:entry.color}}/>}{entry.label}</span><b>{entry.value}</b></div>)}</div>,document.body);
}

export function TrendChart({data,compact=false}) {
  const id=useId().replaceAll(':',''),[active,setActive]=useState(null);
  const tooltip=useChartTooltip();
  const width=720,height=compact?210:258,pad={left:42,right:18,top:18,bottom:35};
  const max=Math.max(25,Math.ceil(Math.max(...data.map(d=>d.total))/25)*25);
  const x=i=>pad.left+i*(width-pad.left-pad.right)/11,y=v=>pad.top+(1-v/max)*(height-pad.top-pad.bottom);
  const points=key=>data.map((d,i)=>`${x(i)},${y(d[key])}`).join(' ');
  const idx=active??11,d=data[idx];
  const showMonth=(e,index)=>{setActive(index);const point=data[index];tooltip.show(e,`${point.label} · 2025`,[
    {label:'Total coletado',value:`${fmt(point.total,2)} t`,color:'#6370e7'},
    {label:'Recicláveis',value:`${fmt(point.reciclavel,2)} t`,color:'#15967d'}])};
  const hide=()=>{setActive(null);tooltip.hide()};
  return <div className="trend-chart"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby={`${id}-title`} tabIndex={0}
    onPointerLeave={hide} onBlur={hide} onFocus={e=>showMonth(e,idx)} onPointerMove={e=>{const r=e.currentTarget.getBoundingClientRect();if(r.width)showMonth(e,Math.max(0,Math.min(11,Math.round(((e.clientX-r.left)*width/r.width-pad.left)/(width-pad.left-pad.right)*11))))}}
    onKeyDown={e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();showMonth(e,Math.max(0,Math.min(11,idx+(e.key==='ArrowRight'?1:-1))))}else if(e.key==='Escape')hide()}}>
    <title id={`${id}-title`}>Toneladas coletadas por mês em 2025. Use as setas para explorar. {data.map(d=>`${d.label}: ${fmt(d.total)} t`).join('; ')}.</title>
    <defs><linearGradient id={`${id}-area`} x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#6370e7" stopOpacity=".23"/><stop offset="100%" stopColor="#6370e7" stopOpacity=".015"/></linearGradient></defs>
    {Array.from({length:5},(_,i)=>{const v=max*i/4;return <g key={i}><line x1={pad.left} x2={width-pad.right} y1={y(v)} y2={y(v)} stroke="#e8edf5" strokeDasharray="3 5"/><text x={pad.left-10} y={y(v)+4} textAnchor="end" className="axis-label">{fmt(v,0)}</text></g>})}
    <polygon points={`${x(0)},${y(0)} ${points('total')} ${x(11)},${y(0)}`} fill={`url(#${id}-area)`}/>
    <polyline points={points('total')} fill="none" stroke="#6370e7" strokeWidth="3.3" strokeLinejoin="round" strokeLinecap="round"/>
    <polyline points={points('reciclavel')} fill="none" stroke="#15967d" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round"/>
    {data.map((point,i)=><g key={i} className="trend-data-points">{['total','reciclavel'].map(key=><circle key={key} cx={x(i)} cy={y(point[key])} r="4" fill={key==='total'?'#6370e7':'#15967d'} stroke="white" strokeWidth="2" onPointerEnter={e=>showMonth(e,i)}/>)}</g>)}
    {active!==null&&<g><line x1={x(idx)} x2={x(idx)} y1={pad.top} y2={y(0)} stroke="#b8bfd7" strokeDasharray="4 4"/><circle cx={x(idx)} cy={y(d.total)} r="5" fill="#6370e7" stroke="white" strokeWidth="3"/><circle cx={x(idx)} cy={y(d.reciclavel)} r="4" fill="#15967d" stroke="white" strokeWidth="2"/></g>}
    {data.map((d,i)=><text key={i} x={x(i)} y={height-10} textAnchor="middle" className="axis-label">{d.label}</text>)}
  </svg><ChartTooltip tip={tooltip.tip}/><div className="chart-reading"><span><i className="dot" style={{background:'#6370e7'}}/>Total coletado</span><span><i className="dot" style={{background:'#15967d'}}/>Recicláveis</span><strong>{d.label}: {fmt(d.total)} t <small>/ {fmt(d.reciclavel)} t recicláveis</small></strong></div></div>;
}

export function Donut({items,totalLabel='toneladas',size=194}) {
  const total=sum(items,'value'),r=73,c=2*Math.PI*r;let offset=0;
  const tooltip=useChartTooltip();
  const showItem=(e,item)=>tooltip.show(e,item.label,[{label:'Peso coletado',value:`${fmt(item.value,2)} t`,color:item.color},{label:'Participação',value:`${fmt(total?item.value/total*100:0,2)}%`}]);
  return <div className="donut-layout"><svg width={size} height={size} viewBox="0 0 200 200" role="img" aria-label={`Composição: ${items.map(x=>`${x.label}, ${fmt(x.value)} toneladas`).join('; ')}`}>
    <circle cx="100" cy="100" r={r} fill="none" stroke="#edf0f7" strokeWidth="22"/>
    {items.map(item=>{const length=total?item.value/total*c:0,start=offset;offset+=length;return <circle key={item.label} cx="100" cy="100" r={r} fill="none" stroke={item.color} strokeWidth="22" strokeDasharray={`${Math.max(0,length-2)} ${c}`} strokeDashoffset={-start} transform="rotate(-90 100 100)" tabIndex={0} aria-label={`${item.label}: ${fmt(item.value,2)} toneladas`} onPointerMove={e=>showItem(e,item)} onPointerLeave={tooltip.hide} onFocus={e=>showItem(e,item)} onBlur={tooltip.hide}/>})}
    <text x="100" y="99" textAnchor="middle" className="donut-total">{fmt(total)}</text><text x="100" y="120" textAnchor="middle" className="donut-caption">{totalLabel}</text>
  </svg><ChartTooltip tip={tooltip.tip}/><div className="donut-legend">{items.map(item=><div key={item.label} tabIndex={0} onPointerMove={e=>showItem(e,item)} onPointerLeave={tooltip.hide} onFocus={e=>showItem(e,item)} onBlur={tooltip.hide}><span><i className="dot" style={{background:item.color}}/>{item.label}</span><strong>{fmt(total?item.value/total*100:0)}<small>%</small></strong></div>)}</div></div>;
}

export function Bars({rows,labelKey,valueKey,color='#6370e7',limit=12,unit='',reverse=false}) {
  const shown=rows.slice(0,limit),max=Math.max(0,...shown.map(r=>num(r[valueKey])));
  const tooltip=useChartTooltip();
  const showRow=(e,row,i)=>tooltip.show(e,String(row[labelKey]),[{label:'Valor',value:row[valueKey]==null?'Sem valor':`${fmt(row[valueKey],Number.isInteger(Number(row[valueKey]))?0:2)}${unit}`,color:typeof color==='function'?color(row,i):color}]);
  return <div className={`bars ${reverse?'bars-compact':''}`} role="img" aria-label={`${valueKey}: ${shown.map(r=>`${r[labelKey]} ${r[valueKey]??'sem valor'}`).join('; ')}`}>
    {shown.map((r,i)=><div className="bar-row" key={i} tabIndex={0} onPointerMove={e=>showRow(e,r,i)} onPointerLeave={tooltip.hide} onFocus={e=>showRow(e,r,i)} onBlur={tooltip.hide}><span className="bar-label">{String(r[labelKey])}</span><div className="bar-track"><div className="bar-fill" style={{width:`${max?Math.max(0,num(r[valueKey]))/max*100:0}%`,background:typeof color==='function'?color(r,i):color}}/></div><strong>{r[valueKey]==null?'—':fmt(r[valueKey],Number.isInteger(Number(r[valueKey]))?0:1)}<small>{unit}</small></strong></div>)}
    <ChartTooltip tip={tooltip.tip}/>
    {!shown.length&&<p className="empty">Nenhum registro para este filtro.</p>}
  </div>;
}

export function RegionChart({rows}) {
  const tooltip=useChartTooltip();
  const regions=[...new Set(rows.map(r=>r.regiao))],palette=['#6370e7','#15967d','#e6b85c','#99a9d4','#d68c8a'];
  const totals=[1,2,3,4].map(q=>sum(rows.filter(r=>num(r.trimestre)===q),'ocorrencias'));
  const max=Math.max(1,...totals);
  return <div className="quarterly"><div className="quarter-bars">{[1,2,3,4].map((q,i)=><div className="quarter" key={q}><strong>{fmt(totals[i],0)}</strong><div className="quarter-stack" style={{height:`${totals[i]/max*160}px`}}>{regions.map((reg,j)=>{const value=sum(rows.filter(r=>r.regiao===reg&&num(r.trimestre)===q),'ocorrencias');const show=e=>tooltip.show(e,`${q}º trimestre · ${reg}`,[{label:'Ocorrências na região',value:fmt(value,0),color:palette[j%palette.length]},{label:'Total do trimestre',value:fmt(totals[i],0)}]);return <div key={reg} style={{height:`${totals[i]?value/totals[i]*100:0}%`,background:palette[j%palette.length]}} tabIndex={0} aria-label={`${q}º trimestre, ${reg}: ${value} ocorrências`} onPointerMove={show} onPointerLeave={tooltip.hide} onFocus={show} onBlur={tooltip.hide}/>})}</div><span>{q}º trimestre</span></div>)}</div><ChartTooltip tip={tooltip.tip}/><div className="chart-reading">{regions.map((r,i)=><span key={r}><i className="dot" style={{background:palette[i%palette.length]}}/>{r}</span>)}</div></div>;
}
