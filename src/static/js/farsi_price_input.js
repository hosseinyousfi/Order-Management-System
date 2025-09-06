(function(){
  function numberWithCommas(x) {
    return x.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function formatInput(input){
    let raw = input.value.replace(/[^0-9]/g, '');
    if (!raw) {
      input.value = '';
      return;
    }
    const posFromEnd = input.value.length - input.selectionStart;
    const withCommas = numberWithCommas(raw);
    input.value = withCommas;
    const newPos = input.value.length - posFromEnd;
    input.setSelectionRange(newPos, newPos);
  }

  function stripCommas(input) {
    input.value = input.value.replace(/,/g, '');
  }

  function initField(input){
    if (input.type === 'number') {
      input.type = 'text';
      input.setAttribute('data-farsi-price', 'true');
    }
    input.setAttribute('inputmode', 'numeric');
    input.addEventListener('input', () => formatInput(input));
    formatInput(input);
  }

  document.addEventListener('DOMContentLoaded', function(){
    const ids = ['id_cost', 'id_payment', 'id_remaining_payment'];
    const inputs = [];

    // by ID
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) inputs.push(el);
    });
    // by CSS (if you have inline widgets)
    document.querySelectorAll('.field-cost input, .field-payment input')
      .forEach(el => { if (!inputs.includes(el)) inputs.push(el); });


    inputs.forEach(initField);

    // now hook the *correct* form
    const adminForm = document.querySelector('#changelist-form');
    const OrderForm = document.querySelector('#order_form');
    if (adminForm) {
      adminForm.addEventListener('submit', () => {
      inputs.forEach(stripCommas);
    });
    }

    
    if (OrderForm) {
      OrderForm.addEventListener('submit', () => {
      inputs.forEach(stripCommas);
    });
    }
  });
})();
