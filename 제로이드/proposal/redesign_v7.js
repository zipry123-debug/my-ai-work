// ② 페르소나 탭: JS가 있을 때만 한 명씩 보여 준다(없으면 전부 펼침)
(function(){
  var sec=document.getElementById("persona"); if(!sec) return;
  var tabs=[].slice.call(sec.querySelectorAll(".ptabs [role=tab]"));
  sec.classList.add("js-tabs");
  function show(id){
    tabs.forEach(function(t){t.setAttribute("aria-selected",t.dataset.p===id?"true":"false");t.tabIndex=t.dataset.p===id?0:-1});
    sec.querySelectorAll(".persona").forEach(function(a){a.classList.toggle("on",a.id===id)});
  }
  tabs.forEach(function(t,i){
    t.addEventListener("click",function(){show(t.dataset.p)});
    t.addEventListener("keydown",function(e){
      var d=e.key==="ArrowRight"?1:e.key==="ArrowLeft"?-1:0; if(!d) return;
      var n=tabs[(i+d+tabs.length)%tabs.length]; n.focus(); show(n.dataset.p); e.preventDefault();
    });
  });
  show("pa");
})();

// ④ 존 구성도: 누른 존의 체험 내용을 옆 패널에 보여 준다
(function(){
  var Z=[
    ["ZONE 0 · 입구","배리어 체크","피부 고민 3문항으로 내 상황에 맞는 체험 1곳을 안내합니다. 진단·측정은 하지 않습니다.","모든 방문객","–","약 4분 (공통 안내)"],
    ["ZONE 1","배리어 리커버리 라운지","거품 세안 시연을 보고 크림을 손등에 발라 봅니다.","A 장벽 회복러","포밍 클렌저 · 인텐시브 크림","약 8분"],
    ["ZONE 2","레드 SOS 바","앰플과 크림 2단계를 차례로 발라 보고 루틴 카드를 받습니다.","B 마감 주간 트러블러","카밍 앰플 · 레드 컨트롤 크림","약 8분"],
    ["ZONE 3","베이스 테스트 미러","크림과 선크림을 바른 뒤 사용감을 비교합니다. 쿠션 협업은 별도 협의.","C 메이크업 베이스 민감러","수딩 크림 · 데일리 선크림","약 8분"],
    ["ZONE 4","미스트 스테이션","분사감과 손등 사용감을 체험합니다. 샘플은 준비 수량 안에서 제공합니다.","D 성수 투어러 · E 주말 러너(가설)","크림 미스트 · 데일리 선크림","약 8분"],
    ["ZONE 5 · 출구","구매 · 온라인 연결","한정 구성 구매 시 파우치를 드리고, QR로 무신사뷰티 온라인 상품에 연결합니다.","모든 방문객","한정 패키지 · 파우치","약 3분"]
  ];
  var btns=[].slice.call(document.querySelectorAll(".floor .fz")), pn=document.querySelector(".zpanel"); if(!pn) return;
  function q(c){return pn.querySelector(c)}
  btns.forEach(function(b){b.addEventListener("click",function(){
    var z=Z[+b.dataset.z];
    btns.forEach(function(x){x.setAttribute("aria-pressed",x===b?"true":"false")});
    q(".zp-n").textContent=z[0];q(".zp-t").textContent=z[1];q(".zp-d").textContent=z[2];
    q(".zp-w").textContent=z[3];q(".zp-p").textContent=z[4];q(".zp-m").textContent=z[5];
  })});
})();

// ⑤ 대시보드: 가정 슬라이더 → 매출·구매자·재구매 재계산
(function(){
  var d=document.querySelector(".dash"); if(!d) return;
  var AOV=35000, BASE={vis:7000,cv:15,on:50,rp:30};
  function $(c){return d.querySelector(c)}
  function f(n){return Math.round(n).toLocaleString("ko-KR")}
  function calc(){
    var vis=+$(".r-vis").value, cv=+$(".r-cv").value, on=+$(".r-on").value, rp=+$(".r-rp").value;
    var buy=vis*cv/100, onl=buy*on/100, rep=onl*rp/100, rev=buy*AOV/10000;
    $(".o-vis").textContent=f(vis)+"명";$(".o-cv").textContent=cv+"%";$(".o-on").textContent=on+"%";$(".o-rp").textContent=rp+"%";
    $(".k-rev").textContent=f(rev)+"만 원";$(".k-buy").textContent=f(buy)+"명";$(".k-onl").textContent=f(onl)+"명";$(".k-rep").textContent=f(rep)+"명";
    $(".f-vis").textContent=f(vis);$(".f-buy").textContent=f(buy);$(".f-onl").textContent=f(onl);$(".f-rep").textContent=f(rep);
    $(".fb-buy").style.width=(cv)+"%";$(".fb-onl").style.width=(cv*on/100)+"%";$(".fb-rep").style.width=(cv*on*rp/10000)+"%";
  }
  d.querySelectorAll("input[type=range]").forEach(function(r){r.addEventListener("input",calc)});
  $(".dash-reset").addEventListener("click",function(){$(".r-vis").value=BASE.vis;$(".r-cv").value=BASE.cv;$(".r-on").value=BASE.on;$(".r-rp").value=BASE.rp;calc()});
  calc();
})();

// 숫자 카운트업: 화면에 들어올 때 0에서 최종값까지(최종값은 처음부터 HTML에 있음)
(function(){
  var els=[].slice.call(document.querySelectorAll("[data-count]"));
  if(!els.length||!("IntersectionObserver" in window)) return;
  if(window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  function fmt(v,dec){return v.toLocaleString("ko-KR",{minimumFractionDigits:dec,maximumFractionDigits:dec})}
  var io=new IntersectionObserver(function(es){es.forEach(function(e){
    if(!e.isIntersecting) return; io.unobserve(e.target);
    var el=e.target, to=+el.dataset.count, dec=+(el.dataset.dec||0), t0=null, dur=900;
    if(!to) return;
    function step(t){t0=t0||t;var k=Math.min(1,(t-t0)/dur);k=1-Math.pow(1-k,3);el.textContent=fmt(to*k,dec);if(k<1)requestAnimationFrame(step);else el.textContent=fmt(to,dec)}
    requestAnimationFrame(step);
  })},{threshold:.4});
  els.forEach(function(el){io.observe(el)});
})();
