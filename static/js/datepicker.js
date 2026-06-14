document.addEventListener('DOMContentLoaded', function () {
    if (typeof flatpickr === 'undefined') {
        return;
    }

    if (flatpickr.l10ns && flatpickr.l10ns.hr) {
        flatpickr.localize(flatpickr.l10ns.hr);
    }

    flatpickr('.flatpickr-date', {
        dateFormat: 'd/m/Y',
        allowInput: true,
    });

    flatpickr('.flatpickr-datetime', {
        enableTime: true,
        dateFormat: 'd/m/Y H:i',
        time_24hr: true,
        allowInput: true,
    });

    const monthInputs = document.querySelectorAll('.flatpickr-month');
    if (monthInputs.length > 0 && typeof monthSelectPlugin !== 'undefined') {
        flatpickr(monthInputs, {
            plugins: [
                new monthSelectPlugin({
                    shorthand: false,
                    dateFormat: 'Y-m',
                    altFormat: 'F Y',
                    altInput: true,
                })
            ],
        });
    }
});