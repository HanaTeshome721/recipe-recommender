document.addEventListener('DOMContentLoaded', () => {
    console.log('Recipe Recommender page loaded successfully!');
});
document.addEventListener('DOMContentLoaded', function() {
    console.log('Signup page loaded.');

    const form = document.querySelector('.signup-form');
    if (form) {
        form.addEventListener('submit', function(event) {
            // You can add client-side validation here if needed
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (!email || !password) {
                console.log("Please fill out all fields.");
                // Prevent form submission if validation fails
                event.preventDefault(); 
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    console.log('Login page loaded.');

    const form = document.querySelector('.login-form');
    if (form) {
        form.addEventListener('submit', function(event) {
            // You can add client-side validation here if needed
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (!email || !password) {
                console.log("Please fill out all fields.");
                // Prevent form submission if validation fails
                event.preventDefault(); 
            }
        });
    }
});