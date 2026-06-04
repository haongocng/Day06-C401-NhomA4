document.addEventListener('DOMContentLoaded', () => {
    const API_BASE = window.location.origin;
    let sessionId = localStorage.getItem('budgetTripSessionId') || crypto.randomUUID();
    localStorage.setItem('budgetTripSessionId', sessionId);

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

    setTheme(localStorage.getItem('theme') === 'dark');
    themeToggleBtn.addEventListener('click', () => {
        setTheme(document.documentElement.getAttribute('data-theme') !== 'dark');
    });

    function toggleSidebar() {
        sidebar.classList.toggle('collapsed');
        openSidebarBtn.style.display = sidebar.classList.contains('collapsed') ? 'block' : 'none';
    }
    closeSidebarBtn.addEventListener('click', toggleSidebar);
    openSidebarBtn.addEventListener('click', toggleSidebar);

    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = `${this.scrollHeight}px`;
        if (this.value.trim() === '') this.style.height = 'auto';
    });

    function typeWriter(element, text, speed = 18, onComplete = null) {
        let i = 0;
        element.innerHTML = '';
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

    const welcomeEl = document.querySelector('.typewriter-welcome');
    if (welcomeEl) {
        typeWriter(welcomeEl, 'Chào bạn! Mình là Trợ lý Thiết kế Tour. Hãy nhập ngân sách, số người, điểm xuất phát và nơi muốn đi; nếu chưa biết đi đâu, mình sẽ gợi ý giúp bạn.');
    }

    function setupCarousel(container) {
        const prevBtn = container.querySelector('.prev-btn');
        const nextBtn = container.querySelector('.next-btn');
        const scrollEl = container.querySelector('.carousel-scroll');
        if (!prevBtn || !nextBtn || !scrollEl) return;
        prevBtn.addEventListener('click', () => {
            const itemWidth = scrollEl.firstElementChild ? scrollEl.firstElementChild.offsetWidth + 12 : 250;
            scrollEl.scrollBy({ left: -itemWidth, behavior: 'smooth' });
        });
        nextBtn.addEventListener('click', () => {
            const itemWidth = scrollEl.firstElementChild ? scrollEl.firstElementChild.offsetWidth + 12 : 250;
            scrollEl.scrollBy({ left: itemWidth, behavior: 'smooth' });
        });
    }

    newTripBtn.addEventListener('click', async () => {
        await fetch(`${API_BASE}/api/sessions/${sessionId}/reset`, { method: 'POST' }).catch(() => {});
        sessionId = crypto.randomUUID();
        localStorage.setItem('budgetTripSessionId', sessionId);
        const messages = chatContainer.querySelectorAll('.message');
        for (let i = 1; i < messages.length; i++) messages[i].remove();
        suggestedPrompts.style.display = 'flex';
        chatInput.value = '';
    });

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
        chatContainer.appendChild(tpl.content.cloneNode(true));
        scrollToBottom();
    }

    function removeSkeletonLoader() {
        const loadingMsg = document.getElementById('loading-msg');
        if (loadingMsg) loadingMsg.remove();
    }

    function formatCurrency(num) {
        return Math.round(Number(num || 0)).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    }

    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = formatCurrency(Math.floor(progress * (end - start) + start));
            if (progress < 1) window.requestAnimationFrame(step);
        };
        window.requestAnimationFrame(step);
    }

    async function callAgent(message) {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, session_id: sessionId })
        });
        if (!response.ok) throw new Error(`API error ${response.status}`);
        const data = await response.json();
        if (data.session_id) {
            sessionId = data.session_id;
            localStorage.setItem('budgetTripSessionId', sessionId);
        }
        return data;
    }

    async function handleSend() {
        const text = chatInput.value.trim();
        if (!text) return;

        suggestedPrompts.style.display = 'none';
        addUserMessage(text);
        chatInput.value = '';
        chatInput.style.height = 'auto';
        addSkeletonLoader();

        try {
            const data = await callAgent(text);
            removeSkeletonLoader();
            renderAgentResponse(data);
        } catch (error) {
            removeSkeletonLoader();
            addSimpleAIMessage('Backend chưa phản hồi. Bạn kiểm tra FastAPI server đang chạy ở cổng 8000 nhé.');
        }
    }

    sendBtn.addEventListener('click', handleSend);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    function addSimpleAIMessage(text) {
        const wrapper = document.createElement('div');
        wrapper.className = 'message ai-message';
        wrapper.innerHTML = `
            <div class="avatar-ai"><i class="ph ph-sparkle"></i></div>
            <div class="message-content"><p class="ai-text-response"></p></div>
        `;
        chatContainer.appendChild(wrapper);
        typeWriter(wrapper.querySelector('.ai-text-response'), text, 12);
        scrollToBottom();
    }

    function renderAgentResponse(data) {
        if (['missing_required_input', 'out_of_scope', 'unsupported_destination', 'text_answer'].includes(data.response_type)) {
            addSimpleAIMessage(data.message || data.follow_up_question || 'Mình cần thêm thông tin trước khi xử lý tiếp.');
            return;
        }
        renderItinerary(data);
    }

    function renderItinerary(data) {
        const tpl = document.getElementById('tpl-happy-path');
        const clone = tpl.content.cloneNode(true);
        const dest = data.city || data.captured_fields?.city_or_area || 'điểm đến';
        const budget = data.captured_fields?.budget_cap || 0;
        const cost = data.cost_summary || {};
        const totalCost = cost.total_cost || 0;
        const itinerary = data.itinerary || [];
        const enrichment = data.enrichment || {};

        const replyText = data.budget_message
            ? `Mình đã lập lịch trình ${dest} theo ngân sách của bạn. ${data.budget_message}`
            : `Mình đã lập lịch trình ${dest} theo yêu cầu của bạn.`;

        setupImages(clone, dest);
        setupWeather(clone, dest, enrichment.weather || {});
        setupBudget(clone, budget, cost);
        setupTimeline(clone, itinerary);
        setupReviews(clone, enrichment.reviews || {});

        chatContainer.appendChild(clone);
        const appendedMessage = chatContainer.lastElementChild;
        const typeTarget = appendedMessage.querySelector('.typewriter-target');
        appendedMessage.querySelectorAll('.dest-name').forEach(n => n.textContent = dest);
        ['#image-carousel', '#review-carousel'].forEach(selector => {
            const carousel = appendedMessage.querySelector(selector);
            if (carousel) setupCarousel(carousel);
        });

        scrollToBottom();
        typeWriter(typeTarget, replyText, 18, () => {
            const fadeElements = appendedMessage.querySelectorAll('.fade-in.hidden');
            fadeElements.forEach((el, index) => {
                setTimeout(() => {
                    el.classList.remove('hidden');
                    scrollToBottom();
                    if (el.querySelector('.progress-bar-container')) {
                        animateBudgetBars(el, budget, totalCost, cost);
                    }
                }, index * 220);
            });
        });
    }

    function setupImages(root, dest) {
        const gallery = root.querySelector('.image-gallery');
        const seed = encodeURIComponent(dest.replace(/ /g, '').toLowerCase());
        gallery.innerHTML = [1, 2, 3, 4].map((index) => `
            <div class="image-wrapper">
                <img src="https://picsum.photos/seed/${seed}${index}/400/300" alt="Ảnh ${index}">
                <div class="image-overlay">${index === 1 ? `Trung tâm ${dest}` : index === 2 ? 'Ẩm thực địa phương' : index === 3 ? 'Cảnh quan' : 'Văn hóa địa phương'}</div>
            </div>
        `).join('');
    }

    function setupWeather(root, dest, weather) {
        const widget = root.querySelector('.weather-widget');
        const tempEl = widget.querySelector('.w-deg');
        const descEl = widget.querySelector('.weather-desc');
        const tempMatch = (weather.summary || '').match(/(-?\d+)°C/);
        tempEl.textContent = tempMatch ? tempMatch[1] : '--';
        descEl.textContent = weather.summary || `Kiểm tra thời tiết ${dest} trước khi đi.`;
    }

    function setupBudget(root, budget, cost) {
        root.querySelector('.total-amount').textContent = '0';
        root.querySelector('.max-budget').textContent = '0';
        const totalEl = root.querySelector('.budget-total');
        if ((cost.total_cost || 0) > budget) {
            totalEl.classList.remove('text-success');
            totalEl.classList.add('text-danger');
        }
    }

    function animateBudgetBars(card, budget, totalCost, cost) {
        const denominator = Math.max(totalCost, budget, 1);
        card.querySelector('.food-bar').style.width = `${Math.min(((cost.food_cost || 0) + (cost.cafe_cost || 0)) / denominator * 100, 100)}%`;
        card.querySelector('.transport-bar').style.width = `${Math.min((cost.transport_cost || 0) / denominator * 100, 100)}%`;
        card.querySelector('.sight-bar').style.width = `${Math.min((cost.activity_cost || 0) / denominator * 100, 100)}%`;
        animateValue(card.querySelector('.total-amount'), 0, totalCost, 1100);
        animateValue(card.querySelector('.max-budget'), 0, budget, 1100);
    }

    function setupTimeline(root, itinerary) {
        const timeline = root.querySelector('#timeline-container');
        timeline.innerHTML = '';
        itinerary.forEach(item => {
            const iconInfo = iconForType(item.type);
            const total = Number(item.average_cost_per_person || 0);
            const div = document.createElement('div');
            div.className = 'timeline-item';
            div.innerHTML = `
                <div class="time">${item.recommended_time_slot || 'Linh hoạt'}</div>
                <div class="activity"><i class="ph ${iconInfo.icon} ${iconInfo.type}"></i> ${item.name || 'Hoạt động'}</div>
                <div class="cost">${formatCurrency(total)}đ/người</div>
            `;
            timeline.appendChild(div);
        });
    }

    function iconForType(type) {
        if (['an_sang', 'an_trua', 'an_toi', 'food', 'restaurant'].includes(type)) {
            return { icon: 'ph-fork-knife', type: 'icon-food' };
        }
        if (type === 'cafe') return { icon: 'ph-coffee', type: 'icon-food' };
        return { icon: 'ph-camera', type: 'icon-sight' };
    }

    function setupReviews(root, reviewsData) {
        const reviewsContainer = root.querySelector('#reviews-container');
        const highlights = reviewsData.highlights || [];
        const urls = reviewsData.source_urls || [];
        reviewsContainer.innerHTML = '';
        if (!highlights.length) {
            highlights.push('Chưa có review tổng hợp. Bạn nên kiểm tra thêm nguồn công khai trước khi chốt lịch trình.');
        }
        highlights.forEach((text, index) => {
            const rDiv = document.createElement('div');
            rDiv.className = 'review-card';
            rDiv.innerHTML = `
                <div class="review-header">
                    <span class="reviewer-name">Nguồn tham khảo ${index + 1}</span>
                    <a href="${urls[index] || '#'}" target="_blank" class="review-source globe" title="Nguồn tham khảo"><i class="ph ph-globe"></i></a>
                </div>
                <div class="review-text">"${text}"</div>
                <div class="review-place"><i class="ph ph-map-pin"></i> Review công khai</div>
            `;
            reviewsContainer.appendChild(rDiv);
        });
    }
});
