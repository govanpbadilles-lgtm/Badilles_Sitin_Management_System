// =======================================================
// BIBLE VERSE POPUP — Show on login, random verse each time
// Include this script on admin_dashboard.html and student.html
// Trigger by calling: showBibleVersePopup()
// Auto-triggered if URL has ?show_verse=1 or ?login=success
// =======================================================

(function() {
    var VERSES = [
        { text: "I can do all things through Christ who strengthens me.", ref: "Philippians 4:13" },
        { text: "The Lord is my shepherd; I shall not want.", ref: "Psalm 23:1" },
        { text: "Trust in the Lord with all your heart and lean not on your own understanding.", ref: "Proverbs 3:5" },
        { text: "For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you.", ref: "Jeremiah 29:11" },
        { text: "Be strong and courageous. Do not be afraid; do not be discouraged, for the Lord your God will be with you wherever you go.", ref: "Joshua 1:9" },
        { text: "The Lord is my light and my salvation — whom shall I fear?", ref: "Psalm 27:1" },
        { text: "Cast all your anxiety on him because he cares for you.", ref: "1 Peter 5:7" },
        { text: "But seek first his kingdom and his righteousness, and all these things will be given to you as well.", ref: "Matthew 6:33" },
        { text: "Do not be anxious about anything, but in every situation, present your requests to God with thanksgiving.", ref: "Philippians 4:6" },
        { text: "God is our refuge and strength, an ever-present help in trouble.", ref: "Psalm 46:1" },
        { text: "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.", ref: "John 3:16" },
        { text: "The name of the Lord is a fortified tower; the righteous run to it and are safe.", ref: "Proverbs 18:10" },
        { text: "Come to me, all you who are weary and burdened, and I will give you rest.", ref: "Matthew 11:28" },
        { text: "And we know that in all things God works for the good of those who love him.", ref: "Romans 8:28" },
        { text: "The Lord your God is with you, the Mighty Warrior who saves. He will take great delight in you.", ref: "Zephaniah 3:17" },
        { text: "Let all that you do be done in love.", ref: "1 Corinthians 16:14" },
        { text: "Commit to the Lord whatever you do, and he will establish your plans.", ref: "Proverbs 16:3" },
        { text: "Even though I walk through the darkest valley, I will fear no evil, for you are with me.", ref: "Psalm 23:4" },
        { text: "Ask and it will be given to you; seek and you will find; knock and the door will be opened to you.", ref: "Matthew 7:7" },
        { text: "I praise you because I am fearfully and wonderfully made; your works are wonderful.", ref: "Psalm 139:14" }
    ];

    function getRandomVerse() {
        return VERSES[Math.floor(Math.random() * VERSES.length)];
    }

    window.showBibleVersePopup = function() {
        // Avoid double-showing
        if (document.getElementById('bibleVerseOverlay')) return;

        var verse = getRandomVerse();

        var overlay = document.createElement('div');
        overlay.id = 'bibleVerseOverlay';
        overlay.innerHTML = `
            <div id="bibleVerseCard">
                <div class="bv-glow"></div>
                <div class="bv-cross-icon">&#9771;</div>
                <p class="bv-label">✦ Verse of the Day ✦</p>
                <blockquote class="bv-text">"${verse.text}"</blockquote>
                <p class="bv-ref">${verse.ref}</p>
                <div class="bv-progress-bar"><div class="bv-progress-fill" id="bvProgressFill"></div></div>
                <button class="bv-close-btn" onclick="closeBibleVerse()">Continue</button>
            </div>
        `;

        var style = document.createElement('style');
        style.id = 'bibleVerseStyles';
        style.textContent = `
            #bibleVerseOverlay {
                position: fixed;
                inset: 0;
                z-index: 99999;
                background: rgba(5, 20, 50, 0.78);
                backdrop-filter: blur(8px);
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                animation: bvOverlayIn 0.5s ease forwards;
            }
            @keyframes bvOverlayIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            #bibleVerseCard {
                position: relative;
                background: linear-gradient(160deg, #0d2b55 0%, #1a4f8a 50%, #0f3668 100%);
                border-radius: 24px;
                padding: 48px 44px 38px;
                max-width: 520px;
                width: 100%;
                text-align: center;
                box-shadow:
                    0 0 0 1px rgba(255,255,255,0.1),
                    0 30px 80px rgba(0, 0, 0, 0.5),
                    0 0 60px rgba(100, 160, 255, 0.12);
                overflow: hidden;
                animation: bvCardIn 0.55s cubic-bezier(0.22, 0.68, 0, 1.2) forwards;
                opacity: 0;
            }
            @keyframes bvCardIn {
                from { opacity: 0; transform: translateY(30px) scale(0.93); }
                to   { opacity: 1; transform: translateY(0) scale(1); }
            }
            .bv-glow {
                position: absolute;
                top: -60px; left: 50%;
                transform: translateX(-50%);
                width: 300px; height: 300px;
                background: radial-gradient(circle, rgba(100,160,255,0.18) 0%, transparent 70%);
                pointer-events: none;
            }
            .bv-cross-icon {
                font-size: 44px;
                color: rgba(255,215,100,0.9);
                margin-bottom: 10px;
                display: block;
                text-shadow: 0 0 20px rgba(255,215,100,0.4);
                animation: bvPulse 2.5s ease-in-out infinite;
            }
            @keyframes bvPulse {
                0%,100% { transform: scale(1); opacity: 0.9; }
                50% { transform: scale(1.06); opacity: 1; }
            }
            .bv-label {
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 2px;
                text-transform: uppercase;
                color: rgba(255,215,100,0.75);
                margin: 0 0 20px;
            }
            .bv-text {
                font-family: Georgia, 'Times New Roman', serif;
                font-size: 20px;
                line-height: 1.65;
                color: #ffffff;
                font-style: italic;
                margin: 0 0 18px;
                quotes: none;
                text-shadow: 0 1px 3px rgba(0,0,0,0.3);
            }
            .bv-ref {
                font-size: 14px;
                font-weight: 700;
                color: rgba(255,215,100,0.9);
                letter-spacing: 0.5px;
                margin: 0 0 28px;
            }
            .bv-progress-bar {
                width: 100%;
                height: 3px;
                background: rgba(255,255,255,0.12);
                border-radius: 2px;
                margin-bottom: 20px;
                overflow: hidden;
            }
            .bv-progress-fill {
                height: 100%;
                width: 100%;
                background: linear-gradient(90deg, #ffd564, #fff);
                border-radius: 2px;
                transform-origin: left;
                animation: bvProgress 8s linear forwards;
            }
            @keyframes bvProgress {
                from { transform: scaleX(1); }
                to   { transform: scaleX(0); }
            }
            .bv-close-btn {
                background: rgba(255,255,255,0.12);
                border: 1px solid rgba(255,255,255,0.2);
                color: white;
                padding: 10px 32px;
                border-radius: 30px;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 0.5px;
                cursor: pointer;
                transition: all 0.2s;
                font-family: inherit;
            }
            .bv-close-btn:hover {
                background: rgba(255,255,255,0.22);
                transform: translateY(-1px);
            }
            @media (max-width: 500px) {
                #bibleVerseCard { padding: 36px 24px 28px; }
                .bv-text { font-size: 17px; }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(overlay);

        // Auto-close after 8 seconds
        var timer = setTimeout(function() { closeBibleVerse(); }, 8000);
        overlay._autoCloseTimer = timer;
    };

    window.closeBibleVerse = function() {
        var overlay = document.getElementById('bibleVerseOverlay');
        if (!overlay) return;
        if (overlay._autoCloseTimer) clearTimeout(overlay._autoCloseTimer);
        overlay.style.animation = 'bvOverlayIn 0.4s ease reverse forwards';
        setTimeout(function() {
            overlay.remove();
            var st = document.getElementById('bibleVerseStyles');
            if (st) st.remove();
        }, 380);
    };

    // Auto-trigger on login success.
    // IMPORTANT: Read the URL param RIGHT NOW (synchronously, before DOMContentLoaded)
    // because script.js strips ?login=success via history.replaceState on its own
    // DOMContentLoaded handler — which runs before ours since it loads first.
    var _shouldShowVerse = (function() {
        var params = new URLSearchParams(window.location.search);
        return params.get('login') === 'success' || params.get('show_verse') === '1';
    })();

    document.addEventListener('DOMContentLoaded', function() {
        if (_shouldShowVerse) {
            setTimeout(showBibleVersePopup, 600);
        }
    });
})();