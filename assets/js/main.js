// افکت‌های ساده برای فرم تماس و دکمه‌ها

document.addEventListener('DOMContentLoaded', function() {
    // افکت لرزش دکمه ارسال پیام در فرم تماس
    var contactBtn = document.querySelector('form button[type="submit"]');
    if(contactBtn) {
        contactBtn.addEventListener('mouseenter', function() {
            contactBtn.classList.add('animate-bounce');
        });
        contactBtn.addEventListener('mouseleave', function() {
            contactBtn.classList.remove('animate-bounce');
        });
    }

    // اسکرول نرم برای منو
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});
