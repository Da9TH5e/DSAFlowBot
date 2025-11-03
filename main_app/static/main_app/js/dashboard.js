//dashboard.js

let lang = "select";
let activePolling = null;
let pollingStartTime = null;
let filteredInterval = null;
let filteredTimeout = null;

const MAX_POLLING_DURATION = 2 * 60 * 60 * 1000; // 2 hours
const POLLING_INTERVAL = 60000; // 1 min for fetching process polling
const FILTERED_INTERVAL = 30000; // 30 sec refresh

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie("csrftoken");

// Language selection
document.getElementById("language").addEventListener("change", function() {
    const selectedLanguage = this.value;
    if (selectedLanguage === "select") {
        const section = document.getElementById("roadmap-section");
        if(section) section.hidden = true;
        return;
    }

    // Stop refresh intervals if language changes
    stopAllPolling();
    clearInterval(filteredInterval);
    clearTimeout(filteredTimeout);

    fetch("/set-language/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken
        },
        body: JSON.stringify({ language: selectedLanguage})
    })
    .then(response => response.json())
    .then(data => {
        if(data.redirect) window.location.href = data.redirect;
    })
    .catch(error => console.error("Error:", error));
});

function topicDefinition(language, topicName) {
    fetch('/get_topic/' , {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ language, topic: topicName })
    })
    .then(res => res.json())
    .then(data => {
        const defContainer = document.getElementById('topic-summary');
        if(defContainer) {
            defContainer.textContent = data.summary || 'Definition not avaliable.';
        }
    })
    .catch(err => console.error('Error fetching topic definition:', err));
}

// Roller setup
function setupRoller(topics, lang) {
    const section = document.getElementById("roadmap-section");
    const langEl = document.getElementById("roadmap-lang");
    const list = document.getElementById("roller-list");
    const win = document.getElementById("roller-window");

    if (!topics || !topics.length) return;

    section.hidden = false;
    langEl.textContent = lang.toUpperCase();

    const scrollKey = `scroll_${lang}`;
    const selectionKey = `selection_${lang}`;

    let currentIndex = Math.min(parseInt(localStorage.getItem(scrollKey) || "0", 10), topics.length - 1);
    let selectedIndex = parseInt(localStorage.getItem(selectionKey) || "-1", 10);

    function render() {
        list.innerHTML = "";
        topics.forEach((t, idx) => {
            const li = document.createElement("li");
            li.textContent = t;
            li.dataset.index = idx;

            if (idx === currentIndex) li.classList.add("current");
            else if (Math.abs(idx - currentIndex) === 1) li.classList.add("adjacent");
            else if (Math.abs(idx - currentIndex) === 2) li.classList.add("distant");

            if (idx === selectedIndex) li.classList.add("selected");

            li.addEventListener('click', (e) => {
                e.stopPropagation();
                selectTopic(idx);
            });

            list.appendChild(li);
        });
        centerCurrent();
    }

    function centerCurrent() {
        const items = list.children;
        if (!items[currentIndex]) return;
        const itemHeight = items[currentIndex].offsetHeight;
        const scrollPos = items[currentIndex].offsetTop - (win.offsetHeight / 2) + (itemHeight / 2);
        win.scrollTo({ top: scrollPos, behavior: 'smooth' });
    }

    function showSelectionFeedback(topicName) {
        let feedbackEl = document.getElementById('selection-feedback');
        if (!feedbackEl) {
            feedbackEl = document.createElement('div');
            feedbackEl.id = 'selection-feedback';
            feedbackEl.className = 'selection-indicator';
            document.querySelector('.roller-shell').appendChild(feedbackEl);
        }
        feedbackEl.textContent = `Selected: ${topicName}`;
        feedbackEl.classList.add('show');
        setTimeout(() => feedbackEl.classList.remove('show'), 2000);
    }

    function updateCurrentPosition() {
        const winMiddle = win.scrollTop + (win.offsetHeight / 2);
        let closestIndex = 0, minDistance = Infinity;
        Array.from(list.children).forEach((item, idx) => {
            const itemMiddle = item.offsetTop + (item.offsetHeight / 2);
            const distance = Math.abs(itemMiddle - winMiddle);
            if (distance < minDistance) {
                minDistance = distance;
                closestIndex = idx;
            }
        });
        if (closestIndex !== currentIndex) {
            currentIndex = closestIndex;
            localStorage.setItem(scrollKey, String(currentIndex));
            render();
        }
    }

    function selectTopic(index) {
        stopAllPolling();
        clearInterval(filteredInterval);
        clearTimeout(filteredTimeout);

        selectedIndex = index;
        localStorage.setItem(selectionKey, String(selectedIndex));

        const topicName = topics[selectedIndex];
        showSelectionFeedback(topicName);

        //definition generation
        topicDefinition(lang, topicName);

        // Immediate DB fetch
        fetchFilteredVideos(lang, topicName);

        // Start backend fetching process
        fetch(`/get_videos/?language=${lang}&topic=${encodeURIComponent(topicName)}`)
            .then(res => res.json())
            .then(data => console.log("Background fetch started:", data))
            .catch(err => console.error("Error triggering background fetch:", err));

        // Begin polling for processing updates
        pollForVideos(lang, topicName);

        // Auto-refresh get_filtered_videos every 30 sec
        filteredInterval = setInterval(() => {
            console.log("Refreshing filtered videos...");
            fetchFilteredVideos(lang, topicName);
        }, FILTERED_INTERVAL);

        // Stop auto-refresh after 30 minutes
        filteredTimeout = setTimeout(() => {
            console.log("Stopped 30-min auto-refresh cycle.");
            clearInterval(filteredInterval);
        }, MAX_POLLING_DURATION);

        render();
        console.log("Selected topic:", topicName);
    }

    render();
    win.addEventListener('scroll', updateCurrentPosition);
    window.addEventListener('resize', updateCurrentPosition);
}

function stopAllPolling() {
    if (activePolling) clearTimeout(activePolling);
    activePolling = null;
    pollingStartTime = null;
}

window.pollForVideos = function(language, topicName) {
    const container = document.getElementById("video-container");
    if (!container) return;
    stopAllPolling();
    pollingStartTime = Date.now();
    const loader = document.createElement("div");
    loader.className = "loader";
    loader.innerHTML = `<div class="spinner"></div>`;
    container.innerHTML = "";
    container.appendChild(loader);
    pollForVideosResults(language, topicName);
}

function pollForVideosResults(language, topicName) {
    const container = document.getElementById("video-container");
    if (!container) return;

    const elapsedTime = Date.now() - pollingStartTime;
    if (elapsedTime >= MAX_POLLING_DURATION) {
        container.innerHTML = "<p>Auto-refresh stopped after 30 minutes. Select the topic again to refresh.</p>";
        return;
    }

    fetch(`/get_filtered_videos/?language=${language}&topic=${encodeURIComponent(topicName)}`)
        .then(res => res.json())
        .then(data => {
            renderVideos(container, data);
            if (data.fetching) {
                activePolling = setTimeout(() => pollForVideosResults(language, topicName), POLLING_INTERVAL);
            }
        })
        .catch(err => {
            container.innerHTML = "<p>Error fetching videos.</p>";
            activePolling = setTimeout(() => pollForVideosResults(language, topicName), POLLING_INTERVAL);
        });
}

function renderVideos(container, data) {
    const buttonStates = {};
    container.querySelectorAll(".practice-btn").forEach(btn => {
        buttonStates[btn.dataset.videoId] = !btn.hidden;
    });

    container.innerHTML = "";

    if (data.status === "ok" && data.videos && data.videos.length > 0) {
        data.videos.forEach(video => {
            const card = document.createElement("div");
            card.className = "video-card";

            card.innerHTML = `
                <a href="${video.url}" target="_blank">
                    <img src="https://img.youtube.com/vi/${video.video_id}/0.jpg" 
                        alt="thumbnail-${video.title}" class="thumbnail">
                    <div class="video-info">
                        <h3 class="video-title">${video.title}</h3>
                        <p class="video-desc">${video.description || ""}</p>
                    </div>
                </a>
                <button class="practice-btn" data-video-id="${video.video_id}" 
                    ${buttonStates[video.video_id] ? "" : "hidden"}>Practice</button>
            `;

            container.appendChild(card);

            const practiceBtn = card.querySelector(".practice-btn");
            const videoLink = card.querySelector("a");

            videoLink.addEventListener("click", () => practiceBtn.hidden = false);

            practiceBtn.addEventListener("click", () => {
                const url = `/questions/?video_id=${video.video_id}`;
                window.open(url, "_blank");
            });
        });

        const countEl = document.getElementById("video-count");
        if (countEl) countEl.textContent = `Total videos: ${data.videos.length}`;
    } else {
        container.innerHTML = `<p class="loading-text">Loading videos<span class="dots"></span></p>`;

        const dotsEl = container.querySelector(".dots");
        let dots = 0;
        const dotInterval = setInterval(() => {
            dots = (dots + 1) % 4;
            dotsEl.textContent = ".".repeat(dots);
        }, 500);
    }
}


function fetchFilteredVideos(language, topicName) {
    const container = document.getElementById("video-container");
    if (!container) return;

    fetch(`/get_filtered_videos/?language=${language}&topic=${encodeURIComponent(topicName)}`)
        .then(res => res.json())
        .then(data => renderVideos(container, data))
        .catch(err => container.innerHTML = "<p>Error fetching videos.</p>");
}

window.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    lang = params.get("language") || "select";

    document.getElementById("language").value = lang;

    if (lang === "select") {
        const section = document.getElementById("roadmap-section");
        if(section) section.hidden = true;
        return;
    }

    fetch(`/roadmap/?language=${lang}`)
        .then(res => res.json())
        .then(data => {
            const raw = data?.roadmap?.topics;
            let topics = [];
            if (Array.isArray(raw)) {
                if (typeof raw[0] === "string") topics = raw;
                else if (raw[0] && typeof raw[0] === "object" && "name" in raw[0]) {
                    topics = raw.map(t => t.name);
                }
            }
            setupRoller(topics, lang);
        })
        .catch(err => console.error("Error loading roadmap:", err));

    window.addEventListener("beforeunload", () => {
        stopAllPolling();
        clearInterval(filteredInterval);
        clearTimeout(filteredTimeout);
    });
});

document.getElementById("generate-roadmap-btn").addEventListener("click", async () => {
    const language = document.getElementById("language").value;
    if (!language || language === "select") {
        alert("Please select a language first!");
        return;
    }

    try {
        const response = await fetch("/generate_roadmap/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken,
            },
            body: JSON.stringify({ language }),
        });

        const data = await response.json();

        if (response.ok) {
            console.log("New roadmap generated:", data);
            showTopAlert("Roadmap generated successfully!");

            setTimeout(async () => {
                try {
                    const fetchResponse = await fetch(`/roadmap/?language=${language}`);
                    const roadmapData = await fetchResponse.json();
                    const raw = roadmapData?.roadmap?.topics;
                    let topics = [];
                    if (Array.isArray(raw)) {
                        if (typeof raw[0] === "string") topics = raw;
                        else if (raw[0] && typeof raw[0] === "object" && "name" in raw[0]) {
                            topics = raw.map(t => t.name);
                        }
                    }
                    setupRoller(topics, language);
                } catch (err) {
                    console.error("Error fetching updated roadmap:", err);
                }
            }, 900);

        } else {
            alert("Error: " + (data.error || "Unknown error"));
        }
    } catch (err) {
        console.error("Error generating roadmap:", err);
    }
});

function showTopAlert(message, color = "#1a1a1a") {
    const alertBox = document.getElementById("top-alert");
    alertBox.textContent = message;
    alertBox.style.backgroundColor = color;

    alertBox.classList.add("show");

    setTimeout(() => {
        alertBox.classList.remove("show");
    }, 2000);
}



