let lastOrderId = {{ orders[0].id if orders else 0 }};
let soundEnabled = true;
let pollInterval = null;

function playNotificationSound() {
  if (!soundEnabled) return;
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 880;
    osc.type = 'sine';
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.5);

    setTimeout(() => {
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.frequency.value = 1108;
      osc2.type = 'sine';
      gain2.gain.setValueAtTime(0.3, ctx.currentTime);
      gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc2.start(ctx.currentTime);
      osc2.stop(ctx.currentTime + 0.5);
    }, 200);
  } catch(e) {}
}

function pollNewOrders() {
  fetch(`/api/orders/new/${COMPUTER_ID}?since=${lastOrderId}`)
    .then(r => r.json())
    .then(orders => {
      if (orders.length > 0) {
        const newIds = orders.map(o => o.id);
        lastOrderId = Math.max(...newIds);
        playNotificationSound();
        orders.forEach(order => {
          showToast(`طلب جديد #${order.order_number}`, 'info');
        });
        setTimeout(() => location.reload(), 1000);
      }
    })
    .catch(() => {});
}

document.addEventListener('DOMContentLoaded', function() {
  if (typeof COMPUTER_ID !== 'undefined') {
    pollInterval = setInterval(pollNewOrders, 3000);
  }
});
