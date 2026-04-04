// ═══════════════════════════════════════════════
//  JAYAM GIFT SHOP — Frontend JS
// ═══════════════════════════════════════════════

const CURRENCY = '₹';

let cartData        = [];
let selectedProduct = null;
let modalQty        = 1;
let activeFilter    = 'all';
let searchTimer     = null;

// ── Init ────────────────────────────────────────
window.addEventListener('load', () => {
  spawnSplashParticles();
  setTimeout(() => {
    const splash = document.getElementById('splash');
    splash.classList.add('hide');
    setTimeout(() => { splash.style.display = 'none'; initHeroCanvas(); }, 800);
  }, 3000);
  loadProducts();
  loadCart();
  initCursor();
  initScrollReveal();
});

// ── SPLASH PARTICLES ────────────────────────────
function spawnSplashParticles() {
  const container = document.getElementById('splash-particles');
  if (!container) return;
  for (let i = 0; i < 40; i++) {
    const p = document.createElement('div');
    const size = Math.random() * 4 + 2;
    Object.assign(p.style, {
      position: 'absolute', width: size+'px', height: size+'px',
      borderRadius: '50%',
      background: `rgba(201,169,110,${Math.random()*.5+.1})`,
      left: Math.random()*100+'%', top: Math.random()*100+'%',
      animation: `fadeIn ${Math.random()*1+.5}s ease ${Math.random()*2}s both, orbFloat ${Math.random()*4+4}s ease-in-out ${Math.random()*3}s infinite`
    });
    container.appendChild(p);
  }
}

// ── HERO CANVAS ──────────────────────────────────
function initHeroCanvas() {
  const canvas = document.getElementById('hero-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let dots = [], W, H;
  function resize() { W = canvas.width = canvas.offsetWidth; H = canvas.height = canvas.offsetHeight; }
  resize();
  window.addEventListener('resize', resize);
  for (let i = 0; i < 60; i++) dots.push({ x:Math.random(), y:Math.random(), vx:(Math.random()-.5)*.0003, vy:(Math.random()-.5)*.0003, r:Math.random()*2+.5, alpha:Math.random()*.5+.15 });
  function draw() {
    ctx.clearRect(0,0,W,H);
    dots.forEach(d => {
      d.x += d.vx; d.y += d.vy;
      if(d.x<0)d.x=1; if(d.x>1)d.x=0; if(d.y<0)d.y=1; if(d.y>1)d.y=0;
      ctx.beginPath(); ctx.arc(d.x*W,d.y*H,d.r,0,Math.PI*2);
      ctx.fillStyle=`rgba(201,169,110,${d.alpha})`; ctx.fill();
    });
    for(let i=0;i<dots.length;i++) for(let j=i+1;j<dots.length;j++) {
      const dx=(dots[i].x-dots[j].x)*W, dy=(dots[i].y-dots[j].y)*H;
      const dist=Math.sqrt(dx*dx+dy*dy);
      if(dist<100){ ctx.beginPath(); ctx.strokeStyle=`rgba(201,169,110,${.15*(1-dist/100)})`; ctx.lineWidth=.5; ctx.moveTo(dots[i].x*W,dots[i].y*H); ctx.lineTo(dots[j].x*W,dots[j].y*H); ctx.stroke(); }
    }
    requestAnimationFrame(draw);
  }
  draw();
}

// ── CURSOR ───────────────────────────────────────
function initCursor() {
  const cursor=document.getElementById('cursor'), dot=document.getElementById('cursor-dot');
  if(!cursor||window.matchMedia('(pointer: coarse)').matches) return;
  let mx=0,my=0,cx=0,cy=0;
  document.addEventListener('mousemove',e=>{ mx=e.clientX; my=e.clientY; dot.style.left=mx+'px'; dot.style.top=my+'px'; });
  function anim(){ cx+=(mx-cx)*.12; cy+=(my-cy)*.12; cursor.style.left=cx+'px'; cursor.style.top=cy+'px'; requestAnimationFrame(anim); }
  anim();
  document.querySelectorAll('button,.product-card,.filter-btn,.nav-link,a').forEach(el=>{
    el.addEventListener('mouseenter',()=>cursor.classList.add('hovering'));
    el.addEventListener('mouseleave',()=>cursor.classList.remove('hovering'));
  });
}

// ── SCROLL REVEAL ────────────────────────────────
function initScrollReveal() {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => { if(e.isIntersecting){ e.target.style.animationPlayState='running'; obs.unobserve(e.target); } });
  }, { threshold: 0.1 });
  document.querySelectorAll('.product-card').forEach((el,i) => {
    el.style.animationDelay = (i*0.07)+'s';
    el.style.animationPlayState = 'paused';
    obs.observe(el);
  });
}

// ── PRODUCTS ─────────────────────────────────────
async function loadProducts(category='all', search='') {
  const grid = document.getElementById('products-grid');
  if (!grid) return;
  grid.innerHTML = `<div class="skeleton-grid">${Array.from({length:6},(_,i)=>`<div class="skeleton-card" style="--d:${i*.08}s"></div>`).join('')}</div>`;
  try {
    const res = await fetch('/api/products?'+new URLSearchParams({category,search}));
    const products = await res.json();
    const cnt = document.getElementById('product-count');
    if(cnt) cnt.textContent = products.length+' items';
    renderProducts(products);
  } catch(e) {
    grid.innerHTML = '<p style="color:var(--ink-light);padding:2rem">Could not load products.</p>';
  }
}

function renderProducts(products) {
  const grid = document.getElementById('products-grid');
  if(!products.length){ grid.innerHTML='<p style="color:var(--ink-light);padding:2rem 0;grid-column:1/-1">No gifts found.</p>'; return; }
  grid.innerHTML = products.map((p,i) => {
    const dp = p.sale_price || p.price;
    return `
      <div class="product-card" style="animation-delay:${i*.07}s" onclick="openModal('${p._id}')">
        <div class="product-img" style="background:${p.bg}">
          <span class="product-img-emoji">${p.emoji}</span>
          <div class="card-overlay"></div>
          <span class="product-card-cart"><i class="fa-solid fa-cart-plus"></i></span>
          ${p.tag ? `<span class="product-tag tag-${p.tag}">${p.tag}</span>` : ''}
        </div>
        <div class="product-info">
          <div class="product-name">${p.name}</div>
          <div class="product-desc">${p.desc.slice(0,62)}…</div>
          <div class="product-footer">
            <div class="price">${CURRENCY}${dp}${p.sale_price ? `<span class="price-original">${CURRENCY}${p.price}</span>` : ''}</div>
            <button class="add-btn" onclick="event.stopPropagation();addToCart('${p._id}','${p.name}','${p.emoji}')"><i class="fa-solid fa-cart-plus"></i></button>
          </div>
        </div>
      </div>`;
  }).join('');
  initScrollReveal();
}

function filterProducts(cat, btn) {
  activeFilter = cat;
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  const labels = {all:'All Gifts',wellness:'Wellness',home:'Home & Living',food:'Food & Drink',accessories:'Accessories',stationery:'Stationery'};
  const el = document.getElementById('section-label');
  if(el) el.textContent = labels[cat];
  loadProducts(cat, document.getElementById('search')?.value||'');
}

function searchProducts(val) {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(()=>loadProducts(activeFilter,val), 320);
}

function scrollToProducts() {
  document.getElementById('filters-section')?.scrollIntoView({behavior:'smooth'});
}

// ── CART ─────────────────────────────────────────
async function loadCart() {
  try { const res=await fetch('/api/cart'); cartData=await res.json(); renderCart(); } catch(e){}
}

async function addToCart(productId, name, emoji) {
  try {
    await fetch('/api/cart/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_id:productId})});
    await loadCart(); bumpBadge(); showToast(emoji, `${name} added to cart`);
  } catch(e){ showToast('❌','Could not add item'); }
}

async function changeQty(cartId, currentQty, delta) {
  try {
    await fetch('/api/cart/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cart_id:cartId,qty:currentQty+delta})});
    await loadCart();
  } catch(e){}
}

async function removeItem(cartId) {
  try {
    await fetch('/api/cart/remove',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cart_id:cartId})});
    await loadCart();
  } catch(e){}
}

function renderCart() {
  const count = cartData.reduce((s,x)=>s+x.qty,0);
  const badge = document.getElementById('cart-count');
  if(badge) badge.textContent = count;
  const sub_el = document.getElementById('cart-subtitle');
  if(sub_el) sub_el.textContent = count+(count===1?' item':' items');
  const items  = document.getElementById('cart-items');
  const footer = document.getElementById('cart-footer');
  if(!items) return;
  if(!cartData.length) {
    items.innerHTML=`<div class="cart-empty"><div class="empty-icon"><i class="fa-solid fa-cart-shopping"></i></div><p style="margin-bottom:.5rem">Your cart is empty.</p><p style="font-size:.8rem;color:var(--ink-light)">Start adding beautiful gifts!</p></div>`;
    if(footer) footer.style.display='none'; return;
  }
  if(footer) footer.style.display='block';
  items.innerHTML = cartData.map(item=>`
    <div class="cart-item">
      <div class="cart-item-icon">${item.emoji}</div>
      <div class="cart-item-info">
        <div class="cart-item-name">${item.name}</div>
        <div class="cart-item-price">${CURRENCY}${(item.sale_price||item.price).toFixed(2)}</div>
        <div class="cart-item-qty">
          <button class="qty-btn" onclick="changeQty('${item.cart_id}',${item.qty},-1)">−</button>
          <span class="qty-num">${item.qty}</span>
          <button class="qty-btn" onclick="changeQty('${item.cart_id}',${item.qty},1)">+</button>
          <button class="remove-item" onclick="removeItem('${item.cart_id}')">Remove</button>
        </div>
      </div>
    </div>`).join('');
  const sub = cartData.reduce((s,x)=>s+(x.sale_price||x.price)*x.qty,0);
  const subtotal_el = document.getElementById('subtotal');
  const total_el    = document.getElementById('total');
  if(subtotal_el) subtotal_el.textContent = CURRENCY+sub.toFixed(2);
  if(total_el)    total_el.textContent    = CURRENCY+sub.toFixed(2);
}

function bumpBadge() {
  const b=document.getElementById('cart-count');
  if(!b) return;
  b.classList.remove('bump'); void b.offsetWidth; b.classList.add('bump');
}

function toggleCart() {
  document.getElementById('cart-panel')?.classList.toggle('open');
  document.getElementById('cart-overlay')?.classList.toggle('open');
}

// ── MODAL ─────────────────────────────────────────
async function openModal(productId) {
  try {
    const res=await fetch('/api/products/'+productId);
    selectedProduct=await res.json(); modalQty=1;
    document.getElementById('modal-img').textContent       = selectedProduct.emoji;
    document.getElementById('modal-name').textContent      = selectedProduct.name;
    document.getElementById('modal-desc').textContent      = selectedProduct.desc;
    document.getElementById('modal-category').textContent  = selectedProduct.category.toUpperCase();
    document.getElementById('modal-qty').textContent       = modalQty;
    document.getElementById('modal-img').parentElement.style.background = selectedProduct.bg;
    const price = selectedProduct.sale_price||selectedProduct.price;
    document.getElementById('modal-price').innerHTML =
      `${CURRENCY}${price}${selectedProduct.sale_price?` <span style="text-decoration:line-through;color:var(--ink-light);font-size:.9rem">${CURRENCY}${selectedProduct.price}</span>`:''}`;
    const badges=document.getElementById('modal-badges');
    badges.innerHTML=selectedProduct.tag?`<span class="product-tag tag-${selectedProduct.tag}" style="position:static">${selectedProduct.tag}</span>`:'';
    document.getElementById('modal-overlay').classList.add('open');
  } catch(e){}
}

function modalQtyChange(delta){ modalQty=Math.max(1,modalQty+delta); document.getElementById('modal-qty').textContent=modalQty; }
function closeModal(e){ if(!e||e.target===document.getElementById('modal-overlay')){ document.getElementById('modal-overlay').classList.remove('open'); selectedProduct=null; } }
async function addFromModal() {
  if(!selectedProduct) return;
  for(let i=0;i<modalQty;i++) await fetch('/api/cart/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_id:selectedProduct._id})});
  await loadCart(); bumpBadge();
  showToast(selectedProduct.emoji,`${selectedProduct.name} added (×${modalQty})`);
  closeModal();
}

// ── CHECKOUT ──────────────────────────────────────
function selectPayment(el, val){ document.querySelectorAll('.payment-opt').forEach(o=>o.classList.remove('active')); el.classList.add('active'); document.getElementById('payment').value=val; }
function goCheckout(){ toggleCart(); showCheckout(); }
function showCheckout() {
  document.getElementById('shop-page').style.display        = 'none';
  document.getElementById('checkout-section').style.display = 'block';
  document.getElementById('success-section').style.display  = 'none';
  const sub=cartData.reduce((s,x)=>s+(x.sale_price||x.price)*x.qty,0);
  document.getElementById('order-summary-box').innerHTML =
    '<h3>Order Summary</h3>'+
    cartData.map(item=>`<div class="summary-line"><span>${item.emoji} ${item.name} ×${item.qty}</span><span>${CURRENCY}${((item.sale_price||item.price)*item.qty).toFixed(2)}</span></div>`).join('')+
    `<div class="summary-line" style="margin-top:10px;padding-top:10px;border-top:1px solid var(--sand);font-weight:500"><span>Total</span><span>${CURRENCY}${sub.toFixed(2)}</span></div>`;
}

async function placeOrder() {
  const fname=document.getElementById('fname').value.trim();
  const email=document.getElementById('email').value.trim();
  if(!fname||!email){ showToast('⚠️','Please fill in required fields'); return; }
  const btn=document.querySelector('.submit-btn'), label=document.getElementById('submit-label');
  label.textContent='Placing order…'; btn.disabled=true;
  try {
    const res=await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({customer:{first_name:fname,last_name:document.getElementById('lname').value.trim(),email,address:document.getElementById('address').value.trim(),city:document.getElementById('city').value.trim(),zip:document.getElementById('zip').value.trim(),gift_message:document.getElementById('gift-msg').value.trim(),payment:document.getElementById('payment').value}})});
    const data=await res.json();
    if(data.success){
      document.getElementById('order-num').textContent='Order #'+data.order_number;
      cartData=[]; renderCart();
      document.getElementById('shop-page').style.display        = 'none';
      document.getElementById('checkout-section').style.display = 'none';
      document.getElementById('success-section').style.display  = 'block';
      spawnConfetti();
    } else { showToast('❌',data.error||'Order failed'); }
  } catch(e){ showToast('❌','Could not place order'); }
  finally{ label.textContent='Place Order'; btn.disabled=false; }
}

function showShop() {
  document.getElementById('shop-page').style.display        = 'block';
  document.getElementById('checkout-section').style.display = 'none';
  document.getElementById('success-section').style.display  = 'none';
  loadProducts(activeFilter, document.getElementById('search')?.value||'');
}

// ── CONFETTI ──────────────────────────────────────
function spawnConfetti() {
  const container=document.getElementById('success-confetti');
  if(!container) return;
  const colors=['#c9a96e','#d4756a','#7a9e8c','#f5ede0','#4a3728','#fef3e2'];
  for(let i=0;i<80;i++){
    const p=document.createElement('div'); p.className='confetti-piece';
    const size=Math.random()*10+5;
    Object.assign(p.style,{width:size+'px',height:size+'px',left:Math.random()*100+'%',top:'-20px',background:colors[Math.floor(Math.random()*colors.length)],borderRadius:Math.random()>.5?'50%':'2px',animationDuration:(Math.random()*2+1.5)+'s',animationDelay:(Math.random()*1)+'s'});
    container.appendChild(p); setTimeout(()=>p.remove(),4000);
  }
}

// ── TOAST ─────────────────────────────────────────
let toastTimeout;
function showToast(icon, msg) {
  const toast=document.getElementById('toast');
  document.getElementById('toast-icon').textContent=icon;
  document.getElementById('toast-msg').textContent=msg;
  toast.classList.add('show');
  clearTimeout(toastTimeout);
  toastTimeout=setTimeout(()=>toast.classList.remove('show'),2500);
}
