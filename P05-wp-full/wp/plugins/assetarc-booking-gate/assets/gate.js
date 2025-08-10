
(function(){
  const BASE=(window.ASSETARC_GATE && ASSETARC_GATE.base)||'';
  const CAL=(window.ASSETARC_GATE && ASSETARC_GATE.calendly)||'';

  async function gw(path, opt){
    const res=await fetch(BASE+path, Object.assign({credentials:'include'}, opt||{}));
    try { return await res.json(); } catch(e){ return {ok:false}; }
  }

  async function createInvoice(amount, currency){
    const r=await gw('/bridge/payments/create-invoice/nowpayments', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ amount: amount||1000, currency: currency||'ZAR' })
    });
    return r && r.invoice && (r.invoice.invoice_url || r.invoice.invoice_url) ? r.invoice.invoice_url : null;
  }

  async function availability(){
    // optional; show a simple message until Booking service is wired
    return { ok:true, slots:[{label:'Weekdays 09:00–16:00 (SAST)'}] };
  }

  function renderCalendly(el){
    el.innerHTML='<div class="calendly-inline-widget" data-url="'+CAL+'" style="min-width:320px;height:650px;"></div><script src="https://assets.calendly.com/assets/external/widget.js" async></script>';
  }

  window.AssetArcGate={ mount: async function(rootId){
    const root=document.getElementById(rootId); if(!root) return;
    root.innerHTML='<div id="aa_gate"><div id="aa_avail"></div><button id="aa_pay">Pay to Confirm</button><div id="aa_note" style="margin-top:8px;color:#555">After payment you'll be able to book.</div><div id="aa_cal" style="margin-top:16px;"></div></div>';
    const slots=await availability();
    document.getElementById('aa_avail').textContent= slots.ok ? (slots.slots.map(s=>s.label).join(' • ')) : 'Loading...';
    document.getElementById('aa_pay').onclick=async()=>{
      const url=await createInvoice(); if(!url){ alert('Could not start payment.'); return; }
      window.open(url,'_blank');
      document.getElementById('aa_note').textContent='Once payment is complete, return here to book.';
      // Optionally poll backend/token balance here to auto-reveal Calendly.
    };
    // Reveal Calendly if query has ?paid=1 (success redirect)
    if (new URLSearchParams(window.location.search).get('paid') === '1'){
      renderCalendly(document.getElementById('aa_cal'));
    }
  }};
})();
