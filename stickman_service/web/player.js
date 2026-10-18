/**
 * AI Stickman Web Player & Exporter
 * Supports all 1,500+ Lucide vector props, character accessories, and MP4/WebM export.
 */

// Default Demo Story
let currentStory = {
  title: "Why Coffee Stops Working",
  aspect_ratio: "9:16",
  accessory: "headphones", // straw_hat, red_beanie, glasses, headphones, headband, tie, crown
  scenes: [
    {
      scene_id: 1,
      stage: "THE HOOK",
      badge: "THE CAFFEINE TRAP",
      overlay: "WHY COFFEE STOPS WORKING",
      accent_color: "cyan",
      action: "sit",
      expression: "shocked",
      prop: { name: "coffee", size: 90, animation: "anim-float" },
      duration: 6.0
    },
    {
      scene_id: 2,
      stage: "DISRUPTING ASSUMPTIONS",
      badge: "THE MISCONCEPTION",
      overlay: "COFFEE DOES NOT GIVE YOU ENERGY",
      accent_color: "crimson",
      action: "run",
      expression: "shocked",
      prop: { name: "battery-charging", size: 80, animation: "anim-pulse" },
      duration: 6.5
    },
    {
      scene_id: 3,
      stage: "THE HIDDEN MECHANISM",
      badge: "ADENOSINE BLOCK",
      overlay: "IT ONLY BORROWS TOMORROW'S ENERGY",
      accent_color: "gold",
      action: "shrug",
      expression: "smirk",
      prop: { name: "brain", size: 85, animation: "anim-bounce" },
      duration: 7.0
    },
    {
      scene_id: 4,
      stage: "THE VICIOUS CYCLE",
      badge: "THE CRASH",
      overlay: "MORE CUPS, LESS IMPACT",
      accent_color: "crimson",
      action: "walk",
      expression: "deadpan",
      prop: { name: "flame", size: 80, animation: "anim-pulse" },
      duration: 7.0
    },
    {
      scene_id: 5,
      stage: "THE ULTIMATE TRUTH",
      badge: "THE CURE",
      overlay: "DELAY YOUR FIRST CUP BY 90 MINUTES",
      accent_color: "gold",
      action: "celebrate",
      expression: "smile",
      prop: { name: "clock", size: 85, animation: "anim-spin" },
      duration: 6.5
    },
    {
      scene_id: 6,
      stage: "ELEVATION & DEBATE",
      badge: "COMMENT BELOW",
      overlay: "HOW MANY CUPS DO YOU DRINK A DAY?",
      accent_color: "cyan",
      action: "point",
      expression: "smirk",
      prop: { name: "message-circle-question", size: 80, animation: "anim-bounce" },
      duration: 5.0
    }
  ]
};

// Detect Preloaded Story from story.js / story.json
if (window.STORY_DATA && window.STORY_DATA.scenes && window.STORY_DATA.scenes.length > 0) {
  currentStory = window.STORY_DATA;
}

// Canvas Setup
const canvas = document.getElementById("render-canvas");
const ctx = canvas.getContext("2d");
const videoWrapper = document.getElementById("video-wrapper");

let isWide = false;
let width = 720;
let height = 1280;

function setResolution(wide) {
  isWide = wide;
  if (wide) {
    width = 1280;
    height = 720;
    videoWrapper.className = "video-wrapper ratio-16-9";
    document.getElementById("ratio-badge").innerText = "16:9 Widescreen";
  } else {
    width = 720;
    height = 1280;
    videoWrapper.className = "video-wrapper ratio-9-16";
    document.getElementById("ratio-badge").innerText = "9:16 Vertical";
  }
  canvas.width = width;
  canvas.height = height;
}

setResolution(currentStory.aspect_ratio === "16:9");

// Character Kinematics & Drawing
function drawStickman(t, action, expression, accessory, xOffset = 0) {
  const cx = width / 2 + xOffset * (width / 3);
  const baseScale = isWide ? 0.85 : 1.0;
  const groundY = height * 0.72;

  const headR = 32 * baseScale;
  const torsoLen = 110 * baseScale;
  const legUpper = 65 * baseScale;
  const legLower = 60 * baseScale;
  const armUpper = 55 * baseScale;
  const armLower = 50 * baseScale;
  const shoulderW = 30 * baseScale;

  let hx = cx;
  let hy = groundY - (torsoLen + legUpper + legLower + headR);
  let chestY, pelvisX = hx, pelvisY;
  let elbowL, handL, elbowR, handR, kneeL, footL, kneeR, footR;

  // Actions
  if (action === "run") {
    const cadence = t * 14.0;
    const bob = Math.abs(Math.sin(cadence)) * 12 * baseScale;
    hy += bob;
    chestY = hy + headR + 15 * baseScale;
    pelvisX = hx - 20 * baseScale;
    pelvisY = chestY + torsoLen;

    const angL = Math.sin(cadence) * 0.85;
    const angR = Math.sin(cadence + Math.PI) * 0.85;

    kneeL = [pelvisX + Math.sin(angL) * legUpper, pelvisY + Math.cos(angL) * legUpper];
    footL = [kneeL[0] + Math.sin(angL + 0.6) * legLower, kneeL[1] + Math.cos(angL + 0.6) * legLower];
    kneeR = [pelvisX + Math.sin(angR) * legUpper, pelvisY + Math.cos(angR) * legUpper];
    footR = [kneeR[0] + Math.sin(angR + 0.6) * legLower, kneeR[1] + Math.cos(angR + 0.6) * legLower];

    elbowL = [hx + Math.sin(-angL) * armUpper, chestY + 10 + Math.cos(-angL) * armUpper];
    handL = [elbowL[0] + Math.sin(-angL + 0.9) * armLower, elbowL[1] + Math.cos(-angL + 0.9) * armLower];
    elbowR = [hx + Math.sin(-angR) * armUpper, chestY + 10 + Math.cos(-angR) * armUpper];
    handR = [elbowR[0] + Math.sin(-angR + 0.9) * armLower, elbowR[1] + Math.cos(-angR + 0.9) * armLower];
  } else if (action === "point") {
    chestY = hy + headR + 20 * baseScale;
    pelvisY = chestY + torsoLen - 20 * baseScale;

    kneeL = [pelvisX - 30 * baseScale, pelvisY + legUpper];
    footL = [pelvisX - 40 * baseScale, kneeL[1] + legLower];
    kneeR = [pelvisX + 30 * baseScale, pelvisY + legUpper];
    footR = [pelvisX + 40 * baseScale, kneeR[1] + legLower];

    elbowL = [hx - 45 * baseScale, chestY + 35 * baseScale];
    handL = [hx - 15 * baseScale, pelvisY - 5];
    elbowR = [hx + 40 * baseScale, chestY + 15 * baseScale];
    handR = [hx + 75 * baseScale, chestY + 10 * baseScale];
  } else if (action === "celebrate") {
    const bob = Math.sin(t * 8) * 8 * baseScale;
    hy += bob;
    chestY = hy + headR + 20 * baseScale;
    pelvisY = chestY + torsoLen - 20 * baseScale;

    kneeL = [pelvisX - 45 * baseScale, pelvisY + legUpper];
    footL = [pelvisX - 55 * baseScale, kneeL[1] + legLower];
    kneeR = [pelvisX + 45 * baseScale, pelvisY + legUpper];
    footR = [pelvisX + 55 * baseScale, kneeR[1] + legLower];

    elbowL = [hx - 50 * baseScale, chestY - 30 * baseScale];
    handL = [hx - 75 * baseScale, chestY - 75 * baseScale];
    elbowR = [hx + 50 * baseScale, chestY - 30 * baseScale];
    handR = [hx + 75 * baseScale, chestY - 75 * baseScale];
  } else if (action === "shrug") {
    chestY = hy + headR + 15 * baseScale;
    pelvisY = chestY + torsoLen - 20 * baseScale;

    kneeL = [pelvisX - 20 * baseScale, pelvisY + legUpper];
    footL = [pelvisX - 25 * baseScale, kneeL[1] + legLower];
    kneeR = [pelvisX + 20 * baseScale, pelvisY + legUpper];
    footR = [pelvisX + 25 * baseScale, kneeR[1] + legLower];

    elbowL = [hx - 45 * baseScale, chestY + 20 * baseScale];
    handL = [hx - 65 * baseScale, chestY];
    elbowR = [hx + 45 * baseScale, chestY + 20 * baseScale];
    handR = [hx + 65 * baseScale, chestY];
  } else {
    // Idle
    const breath = Math.sin(t * 2.5) * 3 * baseScale;
    hy += breath;
    chestY = hy + headR + 20 * baseScale;
    pelvisY = chestY + torsoLen - 20 * baseScale;

    elbowL = [hx - shoulderW, chestY + armUpper];
    handL = [hx - shoulderW - 5, elbowL[1] + armLower];
    elbowR = [hx + shoulderW, chestY + armUpper];
    handR = [hx + shoulderW + 5, elbowR[1] + armLower];

    kneeL = [pelvisX - 15 * baseScale, pelvisY + legUpper];
    footL = [pelvisX - 15 * baseScale, kneeL[1] + legLower];
    kneeR = [pelvisX + 15 * baseScale, pelvisY + legUpper];
    footR = [pelvisX + 15 * baseScale, kneeR[1] + legLower];
  }

  // Draw Skeleton Lines
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 4 * baseScale;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  // Head
  ctx.beginPath();
  ctx.arc(hx, hy, headR, 0, Math.PI * 2);
  ctx.stroke();

  // Face Expression
  ctx.fillStyle = "#ffffff";
  if (expression === "smirk") {
    ctx.beginPath();
    ctx.moveTo(hx + 2, hy - 8 * baseScale);
    ctx.lineTo(hx + 12 * baseScale, hy - 5 * baseScale);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(hx + 5 * baseScale, hy + 2, 8 * baseScale, 0, Math.PI);
    ctx.stroke();
  } else if (expression === "shocked") {
    ctx.beginPath();
    ctx.arc(hx + 5 * baseScale, hy - 4 * baseScale, 3 * baseScale, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(hx + 8 * baseScale, hy + 6 * baseScale, 4 * baseScale, 0, Math.PI * 2);
    ctx.stroke();
  } else {
    // Neutral
    ctx.beginPath();
    ctx.arc(hx + 6 * baseScale, hy - 4 * baseScale, 3 * baseScale, 0, Math.PI * 2);
    ctx.fill();
  }

  // Accessories
  if (accessory === "straw_hat") {
    ctx.strokeStyle = "#ffd700";
    ctx.lineWidth = 5 * baseScale;
    // Brim
    ctx.beginPath();
    ctx.moveTo(hx - 45 * baseScale, hy - 15 * baseScale);
    ctx.lineTo(hx + 45 * baseScale, hy - 15 * baseScale);
    ctx.stroke();
    // Crown
    ctx.beginPath();
    ctx.arc(hx, hy - 15 * baseScale, 26 * baseScale, Math.PI, 0);
    ctx.stroke();
    // Red Ribbon
    ctx.strokeStyle = "#ff2d55";
    ctx.lineWidth = 4 * baseScale;
    ctx.beginPath();
    ctx.moveTo(hx - 24 * baseScale, hy - 17 * baseScale);
    ctx.lineTo(hx + 24 * baseScale, hy - 17 * baseScale);
    ctx.stroke();
  } else if (accessory === "red_beanie") {
    ctx.strokeStyle = "#ff2d55";
    ctx.lineWidth = 7 * baseScale;
    ctx.beginPath();
    ctx.arc(hx, hy - 8 * baseScale, 30 * baseScale, Math.PI, 0);
    ctx.stroke();
  } else if (accessory === "headphones") {
    ctx.strokeStyle = "#00dcff";
    ctx.lineWidth = 4 * baseScale;
    // Headband
    ctx.beginPath();
    ctx.arc(hx, hy, headR + 6 * baseScale, Math.PI * 0.9, Math.PI * 2.1);
    ctx.stroke();
    // Ear cups
    ctx.fillStyle = "#00dcff";
    ctx.beginPath();
    ctx.arc(hx - headR - 4, hy, 7 * baseScale, 0, Math.PI * 2);
    ctx.arc(hx + headR + 4, hy, 7 * baseScale, 0, Math.PI * 2);
    ctx.fill();
  } else if (accessory === "crown") {
    ctx.strokeStyle = "#ffd700";
    ctx.lineWidth = 4 * baseScale;
    const cy_top = hy - headR - 10 * baseScale;
    ctx.beginPath();
    ctx.moveTo(hx - 25 * baseScale, hy - headR + 2);
    ctx.lineTo(hx - 30 * baseScale, cy_top);
    ctx.lineTo(hx - 10 * baseScale, cy_top + 10 * baseScale);
    ctx.lineTo(hx, cy_top);
    ctx.lineTo(hx + 10 * baseScale, cy_top + 10 * baseScale);
    ctx.lineTo(hx + 30 * baseScale, cy_top);
    ctx.lineTo(hx + 25 * baseScale, hy - headR + 2);
    ctx.closePath();
    ctx.stroke();
  } else if (accessory === "glasses") {
    ctx.strokeStyle = "#00dcff";
    ctx.lineWidth = 3 * baseScale;
    const gw = 14 * baseScale;
    ctx.strokeRect(hx - gw - 3 * baseScale, hy - 10 * baseScale, gw, 12 * baseScale);
    ctx.strokeRect(hx + 3 * baseScale, hy - 10 * baseScale, gw, 12 * baseScale);
    ctx.beginPath();
    ctx.moveTo(hx - 3 * baseScale, hy - 4 * baseScale);
    ctx.lineTo(hx + 3 * baseScale, hy - 4 * baseScale);
    ctx.stroke();
  } else if (accessory === "headband") {
    ctx.strokeStyle = "#1a1f2c";
    ctx.lineWidth = 6 * baseScale;
    ctx.beginPath();
    ctx.moveTo(hx - headR - 2, hy - 10 * baseScale);
    ctx.lineTo(hx + headR + 2, hy - 10 * baseScale);
    ctx.stroke();
    // Metal plate
    ctx.fillStyle = "#cbd5e1";
    ctx.fillRect(hx - 14 * baseScale, hy - 14 * baseScale, 28 * baseScale, 8 * baseScale);
  } else if (accessory === "tie") {
    ctx.fillStyle = "#ff2d55";
    const neckY = hy + headR;
    ctx.beginPath();
    ctx.moveTo(hx - 4 * baseScale, neckY + 8 * baseScale);
    ctx.lineTo(hx + 4 * baseScale, neckY + 8 * baseScale);
    ctx.lineTo(hx + 8 * baseScale, neckY + 60 * baseScale);
    ctx.lineTo(hx, neckY + 75 * baseScale);
    ctx.lineTo(hx - 8 * baseScale, neckY + 60 * baseScale);
    ctx.closePath();
    ctx.fill();
  }

  // Torso
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 4 * baseScale;
  ctx.beginPath();
  ctx.moveTo(hx, hy + headR);
  ctx.lineTo(pelvisX, pelvisY);
  ctx.stroke();

  // Arms
  const shoulderY = hy + headR + 15 * baseScale;
  ctx.beginPath();
  ctx.moveTo(hx, shoulderY);
  ctx.lineTo(elbowL[0], elbowL[1]);
  ctx.lineTo(handL[0], handL[1]);
  ctx.moveTo(hx, shoulderY);
  ctx.lineTo(elbowR[0], elbowR[1]);
  ctx.lineTo(handR[0], handR[1]);
  ctx.stroke();

  // Legs
  ctx.beginPath();
  ctx.moveTo(pelvisX, pelvisY);
  ctx.lineTo(kneeL[0], kneeL[1]);
  ctx.lineTo(footL[0], footL[1]);
  ctx.moveTo(pelvisX, pelvisY);
  ctx.lineTo(kneeR[0], kneeR[1]);
  ctx.lineTo(footR[0], footR[1]);
  ctx.stroke();
}

// Stage Props & Lucide Injection
const propStage = document.getElementById("prop-stage");
let currentPropName = "";

function updateProp(propSpec, accentColor) {
  if (!propSpec || !propSpec.name) {
    propStage.innerHTML = "";
    currentPropName = "";
    return;
  }

  if (currentPropName === propSpec.name) return;
  currentPropName = propSpec.name;

  const colorMap = {
    cyan: "#00dcff",
    crimson: "#ff2d55",
    gold: "#ffd700",
    emerald: "#10b981",
    violet: "#8b5cf6",
    amber: "#f59e0b"
  };
  const color = colorMap[accentColor] || "#00dcff";
  const size = propSpec.size || 80;
  const anim = propSpec.animation || "anim-float";

  propStage.innerHTML = `
    <div class="lucide-prop ${anim}" style="color: ${color}; width: ${size}px; height: ${size}px;">
      <i data-lucide="${propSpec.name}" style="width: 100%; height: 100%;"></i>
    </div>
  `;

  // Render Lucide SVG icons instantly
  if (window.lucide) {
    lucide.createIcons();
  }
}

// Audio Player for Synced Studio Voiceovers
const audioPlayer = new Audio();
let currentAudioSrc = "";

function playSceneAudio(scene) {
  if (scene && scene.audio_url) {
    if (currentAudioSrc !== scene.audio_url) {
      currentAudioSrc = scene.audio_url;
      audioPlayer.src = scene.audio_url;
      if (isPlaying) {
        audioPlayer.play().catch(e => console.log("Audio autoplay notice:", e));
      }
    }
  } else {
    audioPlayer.pause();
  }
}

// Playback Engine
let isPlaying = false;
let startTime = null;
let currentSceneIndex = 0;
let totalDuration = 0;

function calculateTotalDuration() {
  totalDuration = currentStory.scenes.reduce((acc, s) => acc + s.duration, 0);
  document.getElementById("time-total").innerText = `0:${Math.round(totalDuration)}`;
  
  // Build timeline scene dots
  const container = document.getElementById("scene-indicators");
  container.innerHTML = "";
  currentStory.scenes.forEach((_, i) => {
    const dot = document.createElement("div");
    dot.className = `scene-dot ${i === 0 ? "active" : ""}`;
    dot.id = `dot-${i}`;
    container.appendChild(dot);
  });
}

function updateSceneUI(scene) {
  document.getElementById("stage-badge").innerText = scene.stage;
  document.getElementById("headline-text").innerText = scene.overlay;

  const badgeElem = document.getElementById("stage-badge");
  const cardElem = document.getElementById("headline-card");

  const colors = {
    cyan: { bg: "#00dcff", border: "#00dcff" },
    crimson: { bg: "#ff2d55", border: "#ff2d55" },
    gold: { bg: "#ffd700", border: "#ffd700" },
    emerald: { bg: "#10b981", border: "#10b981" },
    violet: { bg: "#8b5cf6", border: "#8b5cf6" },
    amber: { bg: "#f59e0b", border: "#f59e0b" }
  };
  const c = colors[scene.accent_color] || colors.cyan;
  badgeElem.style.background = c.bg;
  cardElem.style.borderColor = c.border;

  updateProp(scene.prop, scene.accent_color);
  playSceneAudio(scene);

  // Update dots
  document.querySelectorAll(".scene-dot").forEach((d, idx) => {
    d.className = `scene-dot ${idx === currentSceneIndex ? "active" : ""}`;
  });
}

function tick(timestamp) {
  if (!startTime) startTime = timestamp;
  const elapsed = (timestamp - startTime) / 1000;

  if (elapsed >= totalDuration) {
    isPlaying = false;
    audioPlayer.pause();
    document.getElementById("btn-play").innerText = "▶ Replay";
    return;
  }

  // Determine Current Scene
  let acc = 0;
  let activeScene = currentStory.scenes[0];
  for (let i = 0; i < currentStory.scenes.length; i++) {
    acc += currentStory.scenes[i].duration;
    if (elapsed < acc) {
      if (currentSceneIndex !== i) {
        currentSceneIndex = i;
        updateSceneUI(currentStory.scenes[i]);
      }
      activeScene = currentStory.scenes[i];
      break;
    }
  }

  // Update Progress
  const progressPercent = (elapsed / totalDuration) * 100;
  document.getElementById("progress-bar").style.width = `${progressPercent}%`;
  document.getElementById("scrubber-progress").style.width = `${progressPercent}%`;
  document.getElementById("time-current").innerText = `0:${Math.floor(elapsed).toString().padStart(2, "0")}`;

  // Clear Canvas
  ctx.fillStyle = "#0a0c10";
  ctx.fillRect(0, 0, width, height);

  // Draw Ground Line
  ctx.strokeStyle = "rgba(0, 220, 255, 0.4)";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(40, height * 0.72);
  ctx.lineTo(width - 40, height * 0.72);
  ctx.stroke();

  // Draw Animated Stickman
  drawStickman(
    elapsed,
    activeScene.action,
    activeScene.expression,
    currentStory.accessory,
    isWide ? -0.4 : 0.0
  );

  if (isPlaying) {
    requestAnimationFrame(tick);
  }
}

// Event Listeners
document.getElementById("btn-play").addEventListener("click", () => {
  if (isPlaying) {
    isPlaying = false;
    audioPlayer.pause();
    document.getElementById("btn-play").innerText = "▶ Resume";
  } else {
    isPlaying = true;
    startTime = performance.now() - (parseFloat(document.getElementById("scrubber-progress").style.width || 0) / 100) * totalDuration * 1000;
    document.getElementById("btn-play").innerText = "⏸ Pause";
    const sc = currentStory.scenes[currentSceneIndex];
    if (sc && sc.audio_url) {
      if (currentAudioSrc !== sc.audio_url) {
        currentAudioSrc = sc.audio_url;
        audioPlayer.src = sc.audio_url;
      }
      audioPlayer.play().catch(e => console.log("Audio play info:", e));
    }
    requestAnimationFrame(tick);
  }
});

// Interactive Timeline Scrubber Seek
document.getElementById("scrubber-track").addEventListener("click", (e) => {
  const rect = e.currentTarget.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  const newElapsed = ratio * totalDuration;
  startTime = performance.now() - newElapsed * 1000;

  let acc = 0;
  for (let i = 0; i < currentStory.scenes.length; i++) {
    const scDur = currentStory.scenes[i].duration;
    acc += scDur;
    if (newElapsed < acc || i === currentStory.scenes.length - 1) {
      currentSceneIndex = i;
      updateSceneUI(currentStory.scenes[i]);
      if (currentStory.scenes[i].audio_url) {
        const offsetInScene = Math.max(0, newElapsed - (acc - scDur));
        audioPlayer.currentTime = offsetInScene;
        if (isPlaying) audioPlayer.play().catch(e => {});
      }
      break;
    }
  }

  if (!isPlaying) {
    const progressPercent = ratio * 100;
    document.getElementById("progress-bar").style.width = `${progressPercent}%`;
    document.getElementById("scrubber-progress").style.width = `${progressPercent}%`;
    document.getElementById("time-current").innerText = `0:${Math.floor(newElapsed).toString().padStart(2, "0")}`;
    ctx.fillStyle = "#0a0c10";
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = "rgba(0, 220, 255, 0.4)";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(40, height * 0.72);
    ctx.lineTo(width - 40, height * 0.72);
    ctx.stroke();
    drawStickman(newElapsed, currentStory.scenes[currentSceneIndex].action, currentStory.scenes[currentSceneIndex].expression, currentStory.accessory, isWide ? -0.4 : 0.0);
  }
});

document.getElementById("btn-toggle-ratio").addEventListener("click", () => {
  setResolution(!isWide);
  // Re-draw current frame
  drawStickman(0, currentStory.scenes[currentSceneIndex].action, "neutral", currentStory.accessory);
});

// Built-in Video Exporter (WebCodecs / Canvas Stream)
document.getElementById("btn-export").addEventListener("click", () => {
  const stream = canvas.captureStream(30);
  const mediaRecorder = new MediaRecorder(stream, { mimeType: "video/webm; codecs=vp9" });
  const chunks = [];

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) chunks.push(e.data);
  };

  mediaRecorder.onstop = () => {
    const blob = new Blob(chunks, { type: "video/webm" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${currentStory.title.toLowerCase().replace(/[^a-z0-9]/g, "_")}.webm`;
    a.click();
    alert("Video export complete! File downloaded.");
  };

  alert("Starting real-time video recording... The video will play through and download automatically.");
  mediaRecorder.start();
  startTime = performance.now();
  isPlaying = true;
  requestAnimationFrame(tick);

  setTimeout(() => {
    mediaRecorder.stop();
  }, totalDuration * 1000 + 500);
});

// Init
calculateTotalDuration();
updateSceneUI(currentStory.scenes[0]);
// Initial canvas paint
ctx.fillStyle = "#0a0c10";
ctx.fillRect(0, 0, width, height);
ctx.strokeStyle = "rgba(0, 220, 255, 0.4)";
ctx.lineWidth = 3;
ctx.beginPath();
ctx.moveTo(40, height * 0.72);
ctx.lineTo(width - 40, height * 0.72);
ctx.stroke();
drawStickman(0, currentStory.scenes[0].action, currentStory.scenes[0].expression, currentStory.accessory, isWide ? -0.4 : 0.0);
