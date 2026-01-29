document.addEventListener('DOMContentLoaded', function () {
    function pollStatus() {
        fetch(window.location.href, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newContent = doc.querySelector('.container');
                const currentContent = document.querySelector('.container');
                if (newContent && currentContent) {
                    currentContent.innerHTML = newContent.innerHTML;
                }
            });
    }

    const paymentPending = document.querySelector('.text-warning');
    if (paymentPending) {
        setInterval(pollStatus, 3000);
    }
});
