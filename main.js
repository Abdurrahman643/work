console.log('This is from About page.');

document.addEventListener('DOMContentLoaded', function () {
  const forms = document.querySelectorAll('form.needs-validation');

  forms.forEach(form => {
    const inputs = form.querySelectorAll('input, select, textarea');

    inputs.forEach(input => {
      input.addEventListener('input', () => {
        if (input.checkValidity()) {
          input.classList.add('is-valid');
          input.classList.remove('is-invalid');
        } else {
          input.classList.remove('is-valid');
          input.classList.remove('is-invalid');
        }
      });
    });

    form.addEventListener('submit', (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
        inputs.forEach(input => {
          if (!input.checkValidity()) {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
          }
        });
      }
      form.classList.add('was-validated');
    });
  });
});
