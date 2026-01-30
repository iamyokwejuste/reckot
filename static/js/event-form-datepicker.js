let startPicker = null;
let endPicker = null;

window.initDatePickers = function() {
    const startEl = document.getElementById('id_start_at');
    const endEl = document.getElementById('id_end_at');

    if (!startEl || !endEl) return false;
    if (startEl.offsetParent === null) return false;

    if (startPicker && startPicker.destroy) {
        try { startPicker.destroy(); } catch(e) {}
        startPicker = null;
    }
    if (endPicker && endPicker.destroy) {
        try { endPicker.destroy(); } catch(e) {}
        endPicker = null;
    }

    if (startEl._flatpickr) startEl._flatpickr.destroy();
    if (endEl._flatpickr) endEl._flatpickr.destroy();

    const commonConfig = {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        altInput: true,
        altFormat: "F j, Y \\a\\t h:i K",
        time_24hr: false,
        minuteIncrement: 15,
        disableMobile: false,
        allowInput: true,
        clickOpens: true,
        static: true,
        position: "below"
    };

    const formContainer = document.querySelector('.max-w-2xl');
    const getAlpineData = () => Alpine.$data(formContainer);

    const isEditMode = startEl.value && startEl.value.trim() !== '';

    try {
        startPicker = flatpickr(startEl, {
            ...commonConfig,
            minDate: isEditMode ? null : "today",
            defaultDate: startEl.value || null,
            onChange: function(selectedDates, dateStr) {
                const data = getAlpineData();
                if (data) {
                    data.startAt = dateStr;
                    data.clearError('startAt');
                }
                if (selectedDates[0] && endPicker) {
                    endPicker.set('minDate', selectedDates[0]);
                    if (!isEditMode && !endPicker.selectedDates.length) {
                        const defaultEnd = new Date(selectedDates[0]);
                        defaultEnd.setHours(defaultEnd.getHours() + 2);
                        endPicker.setDate(defaultEnd);
                    }
                }
            }
        });

        endPicker = flatpickr(endEl, {
            ...commonConfig,
            minDate: isEditMode ? null : "today",
            defaultDate: endEl.value || null,
            onChange: function(selectedDates, dateStr) {
                const data = getAlpineData();
                if (data) {
                    data.endAt = dateStr;
                    data.clearError('endAt');
                }
            }
        });

        return true;
    } catch(e) {
        return false;
    }
};
