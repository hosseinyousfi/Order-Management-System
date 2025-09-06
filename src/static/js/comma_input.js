document.addEventListener("DOMContentLoaded", function () {
    const formatNumber = (num) => {
        return num.replace(/\D/g, '').replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    };

    const cleanNumber = (num) => {
        return num.replace(/,/g, '');
    };

    document.querySelectorAll('input[name="unit_cost"], input[name="payment"]').forEach(input => {
        // Format initially
        if (input.value) {
            input.value = formatNumber(input.value);
        }

        // Re-format on input
        input.addEventListener('input', () => {
        const oldPos = input.selectionStart;
        const oldRaw = cleanNumber(input.value);
        
        // Get number of digits before old cursor
        let digitsBeforeCursor = input.value.slice(0, oldPos).replace(/\D/g, '').length;

        // Format number
        const formatted = formatNumber(oldRaw);
        input.value = formatted;

        // Set cursor after same number of digits
        let newPos = 0, digitCount = 0;
        for (; newPos < input.value.length; newPos++) {
            if (/\d/.test(input.value[newPos])) digitCount++;
            if (digitCount >= digitsBeforeCursor) break;
        }
        input.setSelectionRange(newPos + 1, newPos + 1);
    });


        // Clean commas before submitting
        input.closest('form').addEventListener('submit', () => {
            input.value = cleanNumber(input.value);
        });
    });
});
