// ─── LearnSphere Global Scripts ───

// Generate content using Claude AI (for generate.html page)
async function generateContent() {
    const topicEl = document.getElementById("topic");
    const levelEl = document.getElementById("level");
    const outputEl = document.getElementById("output");

    if (!topicEl || !outputEl) return;

    const topic = topicEl.value.trim();
    const level = levelEl ? levelEl.value : "beginner";

    if (topic === "") {
        alert("Please enter a topic!");
        return;
    }

    outputEl.textContent = "✦ Generating content... Please wait.";

    try {
        const response = await fetch("/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ topic: topic, level: level })
        });

        const data = await response.json();
        outputEl.textContent = data.result;
    } catch (e) {
        outputEl.textContent = "Error: Could not connect. Make sure Flask is running and API key is set.";
    }
}

// Topic chip click (used on home page)
function pickTopic(t) {
    const inp = document.getElementById('topicInput');
    const form = document.getElementById('searchForm');
    if (inp && form) {
        inp.value = t;
        form.submit();
    }
}

// Copy code block to clipboard
function copyCode(btn) {
    const code = document.getElementById('codeBlock');
    if (!code) return;
    navigator.clipboard.writeText(code.innerText).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = 'Copy', 2000);
    });
}

// Ask AI tutor
async function askAI() {
    const qEl = document.getElementById('aiQ');
    const respEl = document.getElementById('aiResp');
    const topicEl = document.getElementById('currentTopic');

    if (!qEl || !respEl) return;

    const q = qEl.value.trim();
    if (!q) return;

    const topic = topicEl ? topicEl.value : "";

    respEl.className = 'ai-resp show';
    respEl.innerHTML = '<span class="typing">✦ Claude is thinking...</span>';

    try {
        const res = await fetch('/ai_explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic, question: q })
        });
        const data = await res.json();
        respEl.textContent = data.answer;
    } catch (e) {
        respEl.textContent = 'Could not reach AI. Make sure ANTHROPIC_API_KEY is set.';
    }
}

// ─── Quiz Logic ───
let answered = {};
let score = 0;
let totalQ = 0;

function initQuiz() {
    answered = {};
    score = 0;
    totalQ = document.querySelectorAll('.qcard').length;
}

function pick(btn, qi) {
    if (answered[qi]) return;
    answered[qi] = true;

    const card = document.getElementById('qc' + qi);
    const correct = card.getAttribute('data-answer');
    const selected = btn.getAttribute('data-val');
    const fb = document.getElementById('fb' + qi);

    card.querySelectorAll('.opt').forEach(b => b.disabled = true);

    if (selected === correct) {
        btn.classList.add('right');
        card.classList.add('correct');
        fb.textContent = '✅ Correct!';
        fb.className = 'q-fb show c';
        score++;
    } else {
        btn.classList.add('wrong-pick');
        card.classList.add('wrong');
        fb.textContent = '❌ Wrong! Correct: ' + correct;
        fb.className = 'q-fb show w';
        card.querySelectorAll('.opt').forEach(b => {
            if (b.getAttribute('data-val') === correct) b.classList.add('reveal');
        });
    }

    if (Object.keys(answered).length === totalQ) {
        setTimeout(showScore, 700);
    }
}

function showScore() {
    const box = document.getElementById('scoreBox');
    const big = document.getElementById('scoreBig');
    const msg = document.getElementById('scoreMsg');
    const fill = document.getElementById('progFill');
    if (!box) return;

    box.classList.add('show');
    big.textContent = score + '/' + totalQ;

    const pct = Math.round((score / totalQ) * 100);
    fill.style.width = pct + '%';

    if (pct === 100) msg.textContent = '🏆 Perfect score!';
    else if (pct >= 60) msg.textContent = '👍 Good job! Keep it up.';
    else msg.textContent = '📚 Keep studying, you got this!';
}

function retryQuiz() {
    answered = {};
    score = 0;

    document.querySelectorAll('.qcard').forEach(card => {
        card.className = 'qcard';
        card.querySelectorAll('.opt').forEach(b => {
            b.disabled = false;
            b.className = 'opt';
        });
        const qi = card.id.replace('qc', '');
        const fb = document.getElementById('fb' + qi);
        if (fb) { fb.className = 'q-fb'; fb.textContent = ''; }
    });

    const scoreBox = document.getElementById('scoreBox');
    const progFill = document.getElementById('progFill');
    if (scoreBox) scoreBox.classList.remove('show');
    if (progFill) progFill.style.width = '0%';
}

// Init on page load
document.addEventListener('DOMContentLoaded', initQuiz);
