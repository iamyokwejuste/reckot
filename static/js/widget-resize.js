'use strict';

function sendHeight() {
    var height = document.body.scrollHeight;
    parent.postMessage({ type: 'reckot-resize', height: height }, '*');
}

window.addEventListener('load', sendHeight);
window.addEventListener('resize', sendHeight);
