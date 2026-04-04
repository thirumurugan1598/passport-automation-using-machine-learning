// Passport Seva Portal — Main JS

// Auto-dismiss flash messages
setTimeout(() => {
    document.querySelectorAll('.flash').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(-8px)';
        el.style.transition = 'all 0.4s ease';
        setTimeout(() => el.remove(), 400);
    });
}, 5000);

// Smooth progress bar fill animation on load
document.addEventListener('DOMContentLoaded', () => {
    // Trigger ML score bar animations
    setTimeout(() => {
        document.querySelectorAll('.msi-fill').forEach(bar => {
            const w = bar.style.width;
            bar.style.width = '0';
            setTimeout(() => { bar.style.width = w; }, 100);
        });
    }, 200);

    // Aadhaar number formatting in register
    const aadhaarInput = document.querySelector('input[name="aadhaar"]');
    if (aadhaarInput) {
        aadhaarInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '').slice(0, 12);
        });
    }

    // Phone formatting
    document.querySelectorAll('input[name="phone"], input[name="emergency_contact"]').forEach(el => {
        el.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '').slice(0, 10);
        });
    });

    // Pincode formatting
    const pincodeInput = document.querySelector('input[name="pincode"]');
    if (pincodeInput) {
        pincodeInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '').slice(0, 6);
        });
    }

    // Application number uppercase
    const appNoInput = document.querySelector('.track-input');
    if (appNoInput) {
        appNoInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase();
        });
    }

    // Add hover effect to sidebar steps (visual only, navigation is via buttons)
    document.querySelectorAll('.sidebar-step').forEach(step => {
        step.style.cursor = 'default';
    });

    // Animate analytics cards on scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, i) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, i * 60);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.analytics-card, .dash-stat-card, .service-card').forEach((el, i) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(16px)';
        el.style.transition = `opacity 0.4s ease ${i * 0.05}s, transform 0.4s ease ${i * 0.05}s`;
        observer.observe(el);
    });
});
