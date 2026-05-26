const qrInput =
    document.getElementById("qrInput");

const liveDetection =
    document.getElementById(
        "liveDetection"
    );

const liveQRImage =
    document.getElementById(
        "liveQRImage"
    );

const qrColor =
    document.getElementById(
        "qrColor"
    );

const dynamicForm =
    document.getElementById(
        "dynamicForm"
    );

let selectedAction = "text";


// ==========================
// LIVE INPUT
// ==========================

qrInput.addEventListener("input", () => {

    detectSmartType();

});

qrColor.addEventListener("input", () => {

    generateLiveQR();

});


// ==========================
// NORMALIZE URL
// ==========================

function normalizeURL(value) {

    const domainRegex =
        /^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}/;

    const hasProtocol =
        /^(https?:\/\/)/i.test(value);

    if (
        domainRegex.test(value) &&
        !hasProtocol
    ) {

        return "https://" + value;
    }

    return value;
}


// ==========================
// DETECTION ENGINE
// ==========================

function detectSmartType() {

    let value =
        qrInput.value.trim();

    if (value === "") {

        liveDetection.innerHTML = "";

        dynamicForm.innerHTML = "";

        liveQRImage.style.display = "none";

        return;
    }

    value = normalizeURL(value);

    qrInput.value = value;

    let detectedType = "Plain Text";

    let actions = [];

    // PHONE
    if (/^[0-9]{10}$/.test(
        value.replace("+91", "")
    )) {

        detectedType = "Phone Number";

        actions = [
            {
                label: "📞 Call",
                value: "call"
            },
            {
                label: "💬 SMS",
                value: "sms"
            },
            {
                label: "🟢 WhatsApp",
                value: "whatsapp"
            },
            {
                label: "👤 Save Contact",
                value: "vcard"
            }
        ];
    }

    // EMAIL
    else if (
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        .test(value)
    ) {

        detectedType = "Email Address";

        actions = [
            {
                label: "📧 Send Email",
                value: "email"
            }
        ];
    }

    // WEBSITE
    else if (
        value.startsWith("http://") ||
        value.startsWith("https://")
    ) {

        detectedType = "Website URL";

        actions = [
            {
                label: "🌐 Open Website",
                value: "website"
            }
        ];

        if (
            value.includes("instagram.com")
        ) {

            detectedType =
                "Instagram Profile";

            actions = [
                {
                    label:
                        "📸 Open Instagram",

                    value: "instagram"
                }
            ];
        }

        if (
            value.includes("youtube.com") ||
            value.includes("youtu.be")
        ) {

            detectedType =
                "YouTube Video";

            actions = [
                {
                    label:
                        "▶ Watch Video",

                    value: "youtube"
                }
            ];
        }

        if (
            value.includes("wa.me")
        ) {

            detectedType =
                "WhatsApp Chat";

            actions = [
                {
                    label:
                        "🟢 Open WhatsApp",

                    value: "whatsapp"
                }
            ];
        }
    }

    // WIFI
    else if (
        value.toUpperCase()
        .startsWith("WIFI:")
    ) {

        detectedType = "WiFi QR";

        actions = [
            {
                label:
                    "📶 Connect WiFi",

                value: "wifi"
            }
        ];
    }

    // UPI
    else if (
        value.startsWith("upi://")
    ) {

        detectedType = "UPI Payment";

        actions = [
            {
                label:
                    "💳 Pay Now",

                value: "upi"
            }
        ];
    }

    // DEFAULT
    else {

        actions = [
            {
                label:
                    "📋 Copy Text",

                value: "text"
            }
        ];
    }

    renderDetection(
        detectedType,
        actions
    );
}


// ==========================
// RENDER
// ==========================

function renderDetection(
    type,
    actions
) {

    let actionsHTML = "";

    actions.forEach(action => {

        actionsHTML += `

            <div
                class="action-card"
                onclick="
                    selectAction(
                        '${action.value}',
                        this
                    )
                ">

                ${action.label}

            </div>

        `;
    });

    liveDetection.innerHTML = `

        <div class="detect-card">

            <h3>

                ⚡ ${type}

            </h3>

            <div class="action-grid">

                ${actionsHTML}

            </div>

        </div>

    `;

    if (actions.length > 0) {

        selectedAction =
            actions[0].value;

        setTimeout(() => {

            const firstCard =
                document.querySelector(
                    ".action-card"
                );

            if (firstCard) {

                firstCard.classList.add(
                    "active-action"
                );
            }

        }, 50);

        renderDynamicForm(
            selectedAction
        );

        generateLiveQR();
    }
}


// ==========================
// SELECT ACTION
// ==========================

function selectAction(
    action,
    element
) {

    selectedAction = action;

    document
        .querySelectorAll(
            ".action-card"
        )
        .forEach(card => {

            card.classList.remove(
                "active-action"
            );

        });

    element.classList.add(
        "active-action"
    );

    renderDynamicForm(action);

    generateLiveQR();
}


// ==========================
// DYNAMIC FORMS
// ==========================

function renderDynamicForm(action) {

    dynamicForm.innerHTML = "";

    // VCARD
    if (action === "vcard") {

        dynamicForm.innerHTML = `

            <div class="detect-card">

                <h3>
                    👤 Contact Details
                </h3>

                <input
                    type="text"
                    id="contactName"
                    placeholder="Full Name">

                <input
                    type="email"
                    id="contactEmail"
                    placeholder="Email">

                <input
                    type="text"
                    id="contactCompany"
                    placeholder="Company">

            </div>

        `;
    }

    // EMAIL
    if (action === "email") {

        dynamicForm.innerHTML = `

            <div class="detect-card">

                <h3>
                    📧 Email Details
                </h3>

                <input
                    type="text"
                    id="emailSubject"
                    placeholder="Subject">

                <textarea
                    id="emailBody"
                    placeholder="Message"></textarea>

            </div>

        `;
    }

    // LISTENERS
    document
        .querySelectorAll(
            "#dynamicForm input, #dynamicForm textarea"
        )
        .forEach(input => {

            input.addEventListener(
                "input",
                generateLiveQR
            );

        });
}


// ==========================
// LIVE QR
// ==========================

async function generateLiveQR() {

    const input =
        qrInput.value.trim();

    if (input === "") return;

    const response = await fetch(
        "/live-preview",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({

                qrdata: input,

                action: selectedAction,

                color: qrColor.value,

                name:
                    document.getElementById(
                        "contactName"
                    )?.value || "",

                email:
                    document.getElementById(
                        "contactEmail"
                    )?.value || "",

                company:
                    document.getElementById(
                        "contactCompany"
                    )?.value || "",

                subject:
                    document.getElementById(
                        "emailSubject"
                    )?.value || "",

                body:
                    document.getElementById(
                        "emailBody"
                    )?.value || ""

            })
        }
    );

    const result =
        await response.json();

    liveQRImage.src =
        result.qr_image +
        "?t=" +
        new Date().getTime();

    liveQRImage.style.display =
        "block";
}