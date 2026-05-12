document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.clickable-row').forEach(row => {
        row.addEventListener('click', () => {
            window.location = row.dataset.href;
        });
    });
});