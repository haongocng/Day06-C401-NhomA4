document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const sidebar = document.getElementById('sidebar');
    const closeSidebarBtn = document.getElementById('close-sidebar-btn');
    const openSidebarBtn = document.getElementById('open-sidebar-btn');
    const newTripBtn = document.getElementById('new-trip-btn');
    const suggestedPrompts = document.getElementById('suggested-prompts');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const themeIcon = document.getElementById('theme-icon');

    // Theme Toggle Logic
    function setTheme(isDark) {
        if (isDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
            themeIcon.classList.replace('ph-moon', 'ph-sun');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
            themeIcon.classList.replace('ph-sun', 'ph-moon');
            localStorage.setItem('theme', 'light');
        }
    }

    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        setTheme(true);
    } else {
        setTheme(false); // Light is default
    }

    themeToggleBtn.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        setTheme(!isDark);
    });

    // Sidebar Toggle
    function toggleSidebar() {
        sidebar.classList.toggle('collapsed');
        if (sidebar.classList.contains('collapsed')) {
            openSidebarBtn.style.display = 'block';
        } else {
            openSidebarBtn.style.display = 'none';
        }
    }
    
    closeSidebarBtn.addEventListener('click', toggleSidebar);
    openSidebarBtn.addEventListener('click', toggleSidebar);

    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value.trim() === '') {
            this.style.height = 'auto';
        }
    });

    function typeWriter(element, text, speed = 25, onComplete = null) {
        let i = 0;
        function type() {
            if (i < text.length) {
                element.innerHTML += text.charAt(i);
                i++;
                scrollToBottom();
                setTimeout(type, speed);
            } else if (onComplete) {
                onComplete();
            }
        }
        type();
    }

    // Play Welcome Typewriter
    const welcomeEl = document.querySelector('.typewriter-welcome');
    if (welcomeEl) {
        typeWriter(welcomeEl, "Chào bạn! Mình là Trợ lý Thiết kế Tour (Budget Travel Planner AI). 🌍✨ Bạn muốn đi đâu hôm nay? Hãy nhập điểm đến, số ngày và ngân sách, mình sẽ lên kế hoạch chi tiết cho bạn.");
    }

    // Setup Carousel Buttons
    function setupCarousel(container) {
        const prevBtn = container.querySelector('.prev-btn');
        const nextBtn = container.querySelector('.next-btn');
        const scrollEl = container.querySelector('.carousel-scroll');

        if (prevBtn && nextBtn && scrollEl) {
            prevBtn.addEventListener('click', () => {
                const itemWidth = scrollEl.firstElementChild ? scrollEl.firstElementChild.offsetWidth + 12 : 250;
                scrollEl.scrollBy({ left: -itemWidth, behavior: 'smooth' });
            });
            nextBtn.addEventListener('click', () => {
                const itemWidth = scrollEl.firstElementChild ? scrollEl.firstElementChild.offsetWidth + 12 : 250;
                scrollEl.scrollBy({ left: itemWidth, behavior: 'smooth' });
            });
        }
    }

    // New Trip (Clear Chat)
    newTripBtn.addEventListener('click', () => {
        const messages = chatContainer.querySelectorAll('.message');
        for (let i = 1; i < messages.length; i++) {
            messages[i].remove();
        }
        suggestedPrompts.style.display = 'flex';
        chatInput.value = '';
    });

    // Handle Suggested Prompts
    document.querySelectorAll('.prompt-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            chatInput.value = chip.getAttribute('data-prompt');
            chatInput.focus();
            sendBtn.click();
        });
    });

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function addUserMessage(text) {
        const tpl = document.getElementById('tpl-user-msg');
        const clone = tpl.content.cloneNode(true);
        clone.querySelector('.message-content').textContent = text;
        chatContainer.appendChild(clone);
        scrollToBottom();
    }

    function addSkeletonLoader() {
        const tpl = document.getElementById('tpl-skeleton');
        const clone = tpl.content.cloneNode(true);
        chatContainer.appendChild(clone);
        scrollToBottom();
    }

    function removeSkeletonLoader() {
        const loadingMsg = document.getElementById('loading-msg');
        if (loadingMsg) {
            loadingMsg.remove();
        }
    }

    function formatCurrency(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }

    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = formatCurrency(Math.floor(progress * (end - start) + start));
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // Main Chat Logic
    function handleSend() {
        const text = chatInput.value.trim();
        if (!text) return;

        suggestedPrompts.style.display = 'none';

        addUserMessage(text);
        chatInput.value = '';
        chatInput.style.height = 'auto';
        
        addSkeletonLoader();

        // Simulate AI Processing (2.5s to show skeleton effect)
        setTimeout(() => {
            removeSkeletonLoader();
            
            let dest = "Địa điểm của bạn";
            if (text.toLowerCase().includes('đà lạt')) dest = "Đà Lạt";
            else if (text.toLowerCase().includes('phú quốc')) dest = "Phú Quốc";
            else if (text.toLowerCase().includes('sapa')) dest = "Sapa";

            let budget = 1500000;
            if (text.includes('1.5tr') || text.includes('1.5 triệu')) budget = 1500000;
            if (text.includes('3tr') || text.includes('3 triệu')) budget = 3000000;
            if (text.includes('2 triệu')) budget = 2000000;

            generateItinerary(dest, budget);
        }, 2500);
    }

    sendBtn.addEventListener('click', handleSend);

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    function generateItinerary(dest, budget) {
        const tpl = document.getElementById('tpl-happy-path');
        const clone = tpl.content.cloneNode(true);
        
        const aiTextEl = clone.querySelector('.ai-text-response');
        const replyText = `Tuyệt vời! Dưới đây là kế hoạch du lịch ${dest} dành cho bạn. Mình đã tối ưu để vừa vặn với ngân sách nhé. 🎒`;
        
        // Setup Images
        const gallery = clone.querySelector('.image-gallery');
        const seed = dest.replace(/ /g, '').toLowerCase();
        gallery.innerHTML = `
            <div class="image-wrapper">
                <img src="https://picsum.photos/seed/${seed}1/400/300" alt="Ảnh 1">
                <div class="image-overlay">Trung tâm ${dest}</div>
            </div>
            <div class="image-wrapper">
                <img src="https://picsum.photos/seed/${seed}2/400/300" alt="Ảnh 2">
                <div class="image-overlay">Ẩm thực địa phương</div>
            </div>
            <div class="image-wrapper">
                <img src="https://picsum.photos/seed/${seed}3/400/300" alt="Ảnh 3">
                <div class="image-overlay">Cảnh quan thiên nhiên</div>
            </div>
            <div class="image-wrapper">
                <img src="https://picsum.photos/seed/${seed}4/400/300" alt="Ảnh 4">
                <div class="image-overlay">Đời sống văn hóa</div>
            </div>
        `;

        // Mock Budget Calculations
        const foodCost = budget * 0.35;
        const transportCost = budget * 0.25;
        const sightCost = budget * 0.20;
        const totalCost = foodCost + transportCost + sightCost;

        // Timeline items
        const timeline = clone.querySelector('#timeline-container');
        const items = [
            { time: "08:00 AM", act: "Ăn sáng đặc sản địa phương", cost: foodCost * 0.2, icon: "ph-fork-knife", type: "icon-food" },
            { time: "09:00 AM", act: `Di chuyển đến trung tâm ${dest}`, cost: transportCost * 0.4, icon: "ph-taxi", type: "icon-transport" },
            { time: "09:30 AM", act: `Tham quan điểm nổi bật ở ${dest}`, cost: sightCost * 0.5, icon: "ph-camera", type: "icon-sight" },
            { time: "12:00 PM", act: "Ăn trưa & Nghỉ ngơi", cost: foodCost * 0.4, icon: "ph-bowl-food", type: "icon-food" },
            { time: "02:00 PM", act: "Thuê xe máy khám phá xung quanh", cost: transportCost * 0.6, icon: "ph-moped", type: "icon-transport" },
            { time: "06:00 PM", act: "Ăn tối & Dạo chợ đêm", cost: foodCost * 0.4, icon: "ph-storefront", type: "icon-food" }
        ];

        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'timeline-item';
            div.innerHTML = `
                <div class="time">${item.time}</div>
                <div class="activity"><i class="ph ${item.icon} ${item.type}"></i> ${item.act}</div>
                <div class="cost">${formatCurrency(item.cost)}đ</div>
            `;
            timeline.appendChild(div);
        });

        // Reviews Section
        const reviewsContainer = clone.querySelector('#reviews-container');
        const reviews = [
            { name: "Lan Phương", text: `Trải nghiệm quá tuyệt, đồ ăn rẻ mà ngon, phòng ốc sạch sẽ ngay trung tâm ${dest}!`, source: "facebook", icon: "ph-facebook-logo", place: "Homestay Trung Tâm" },
            { name: "Hoàng Tuấn", text: `View check-in bao xịn. Đáng giá tiền vé vào cổng, nhưng cuối tuần hơi đông nhé.`, source: "google", icon: "ph-google-logo", place: "Khu du lịch sinh thái" },
            { name: "Travel Blog VN", text: `Được đánh giá là một trong những điểm must-go khi đến ${dest} năm nay.`, source: "globe", icon: "ph-globe", place: "Cộng đồng Phượt" },
            { name: "Minh Thu", text: `Thời tiết ${dest} đợt này siêu đẹp, đồ ăn ở chợ đêm rất rẻ. Mình tốn có tí xíu tiền! Nói chung là chuyến đi quá mãn nguyện, mình chắc chắn sẽ quay lại. Mình cực kỳ đề xuất các bạn nên thử ăn bánh căn và lẩu gà lá é vì thời tiết se lạnh ăn rất hợp. Ngoài ra các bạn cũng nên chuẩn bị thêm áo ấm và giày thể thao để tiện di chuyển nhé. Điểm 10/10!`, source: "facebook", icon: "ph-facebook-logo", place: "Chợ đêm" }
        ];
        
        reviews.forEach(rv => {
            const rDiv = document.createElement('div');
            rDiv.className = 'review-card';
            rDiv.innerHTML = `
                <div class="review-header">
                    <span class="reviewer-name">${rv.name}</span>
                    <a href="#" class="review-source ${rv.source}" title="Nguồn: ${rv.source}"><i class="ph ${rv.icon}"></i></a>
                </div>
                <div class="review-text">"${rv.text}"</div>
                <div class="review-place"><i class="ph ph-map-pin"></i> ${rv.place}</div>
            `;
            reviewsContainer.appendChild(rDiv);
        });

        chatContainer.appendChild(clone);
        
        // Target the newly appended nodes
        const appendedMessage = chatContainer.lastElementChild;
        const typeTarget = appendedMessage.querySelector('.typewriter-target');
        const destNames = appendedMessage.querySelectorAll('.dest-name');
        destNames.forEach(n => n.textContent = dest);

        // Setup Carousels
        const imageCarousel = appendedMessage.querySelector('#image-carousel');
        const reviewCarousel = appendedMessage.querySelector('#review-carousel');
        if (imageCarousel) setupCarousel(imageCarousel);
        if (reviewCarousel) setupCarousel(reviewCarousel);

        scrollToBottom();

        // Execute Typewriter, then fade in other elements
        typeWriter(typeTarget, replyText, 25, () => {
            const fadeElements = appendedMessage.querySelectorAll('.fade-in.hidden');
            fadeElements.forEach((el, index) => {
                setTimeout(() => {
                    el.classList.remove('hidden');
                    scrollToBottom();
                    
                    if (el.querySelector('.progress-bar-container')) {
                        const foodBar = el.querySelector('.food-bar');
                        const transportBar = el.querySelector('.transport-bar');
                        const sightBar = el.querySelector('.sight-bar');
                        
                        setTimeout(() => {
                            foodBar.style.width = '35%';
                            transportBar.style.width = '25%';
                            sightBar.style.width = '20%';
                        }, 100);

                        animateValue(el.querySelector('.total-amount'), 0, totalCost, 1500);
                        animateValue(el.querySelector('.max-budget'), 0, budget, 1500);
                    }
                }, index * 300);
            });
        });
    }
});
