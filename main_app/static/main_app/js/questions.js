const questionsGrid = document.getElementById("questions-grid");
const editorContainer = document.getElementById("editor-container");
const backButton = document.getElementById("back-button");
const editorTitle = document.getElementById("editor-title");
const questionContent = document.getElementById("question-content");
const codeArea = document.getElementById("code-area");

const params = new URLSearchParams(window.location.search);
const video_id = params.get("video_id");

// Function to auto-expand textarea
function autoExpand(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight + 2) + 'px';
}

// Back button functionality
backButton.addEventListener('click', function() {
    editorContainer.classList.add('hidden');
    questionsGrid.classList.remove('hidden');
    document.title = "Practice Questions";
});

if (!video_id) {
    questionsGrid.innerHTML = "<p style='color: #ccc; padding: 20px;'>No video selected.</p>";
} else {
    fetch(`/get_questions/?video_id=${video_id}`)
        .then(res => res.json())
        .then(data => {
            if (data.status === "ok" && data.questions.length) {
                data.questions.forEach((q, index) => {
                    const questionSquare = document.createElement("div");
                    questionSquare.className = "question-square";
                    questionSquare.dataset.questionId = index;

                    // Determine question type
                    const fields = [
                        q.input_format,
                        q.output_format,
                        q.example_input,
                        q.example_output
                    ];

                    const emptyCount = fields.filter(f => 
                        !f || 
                        f.trim() === "" || 
                        f.trim().toLowerCase() === "none"
                    ).length;

                    const isCodingQuestion = emptyCount < 3;
                    const questionType = isCodingQuestion ? "Coding" : "Theory";

                    questionSquare.innerHTML = `
                        <div>
                            <div class="question-title">Question ${index + 1}: </div>
                            <div class="question-desc">${q.description}</div>
                        </div>
                        <div class="question-type">${questionType}</div>
                    `;

                    // Click event for question square
                    questionSquare.addEventListener('click', function() {
                        const rect = questionSquare.getBoundingClientRect();
                        
                        // Position editor on top of clicked square
                        editorContainer.style.top = rect.top + 'px';
                        editorContainer.style.left = rect.left + 'px';
                        editorContainer.style.width = rect.width + 'px';
                        editorContainer.style.height = rect.height + 'px';
                        editorContainer.style.transform = 'scale(0.5)';
                        editorContainer.style.opacity = '0';
                        editorContainer.classList.remove('hidden');
                        editorContainer.classList.add('animating');

                        // Force reflow to allow transition
                        editorContainer.getBoundingClientRect();

                        // Animate to center/lower area
                        setTimeout(() => {
                            editorContainer.style.top = '22%';
                            editorContainer.style.left = '50%';
                            editorContainer.style.width = '95%';
                            editorContainer.style.height = '75%';
                            editorContainer.style.transform = 'translateX(-50%) scale(1)';
                            editorContainer.style.opacity = '1';
                        }, 50);

                        // After animation ends, remove animating class
                        setTimeout(() => editorContainer.classList.remove('animating'), 600);

                        // Update page title
                        document.title = `${q.title} - Practice Questions`;

                        // Set editor title
                        editorTitle.textContent = `Question ${index + 1}`;

                        // Build question content
                        let contentHtml = `<p><strong>Description:</strong> ${q.description}</p>`;
                        if (isCodingQuestion) {
                            if (q.input_format && q.input_format.trim() !== "" && q.input_format.trim().toLowerCase() !== "none")
                                contentHtml += `<p><strong>Input Format:</strong><br>${q.input_format}</p>`;
                            if (q.output_format && q.output_format.trim() !== "" && q.output_format.trim().toLowerCase() !== "none")
                                contentHtml += `<p><strong>Output Format:</strong><br>${q.output_format}</p>`;
                            if (q.example_input && q.example_input.trim() !== "" && q.example_input.trim().toLowerCase() !== "none")
                                contentHtml += `<p><strong>Example Input:</strong><br><code>${q.example_input}</code></p>`;
                            if (q.example_output && q.example_output.trim() !== "" && q.example_output.trim().toLowerCase() !== "none")
                                contentHtml += `<p><strong>Example Output:</strong><br><code>${q.example_output}</code></p>`;
                        } else {
                            contentHtml += `<p><em>This is a descriptive/theory question. No coding required.</em></p>`;
                        }

                        questionContent.innerHTML = contentHtml;

                        codeArea.value = "";
                        setTimeout(() => {
                            codeArea.style.height = "100%";
                            codeArea.focus();
                        }, 100);
                    });

                    questionsGrid.appendChild(questionSquare);
                });
            } else {
                questionsGrid.innerHTML = "<p style='color: #ccc; padding: 20px;'>No questions found for this video.</p>";
            }
        })
        .catch(err => {
            questionsGrid.innerHTML = "<p style='color: #ccc; padding: 20px;'>Error fetching questions.</p>";
            console.error(err);
        });
}

document.addEventListener("DOMContentLoaded", function () {
    const runBtn = document.getElementById("run-code-btn");
    const codeArea = document.querySelector("#code-area textarea");
    const languageSelect = document.getElementById("language");
    const outputDiv = document.getElementById("output");

    runBtn.addEventListener("click", async () => {
        const code = codeArea.value.trim();
        const language = languageSelect.value;

        if (!code) {
            outputDiv.textContent = "⚠️ Please write some code first!";
            return;
        }

        outputDiv.textContent = "⏳ Running your code...";

        try {
            const response = await fetch("/run_code/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken(),
                },
                body: JSON.stringify({
                    source_code: code,
                    language: language,
                }),
            });

            const data = await response.json();
            if (data.error) {
                outputDiv.textContent = `❌ ${data.error}`;
            } else {
                outputDiv.textContent =
                    (data.stdout || data.compile_output || data.stderr || "No output") +
                    `\n\nStatus: ${data.status}`;
            }
        } catch (error) {
            console.error("Error:", error);
            outputDiv.textContent = "❌ Error running code.";
        }
    });

    function getCSRFToken() {
        const name = "csrftoken";
        const cookies = document.cookie.split(";").map(c => c.trim());
        for (let cookie of cookies) {
            if (cookie.startsWith(name + "=")) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return "";
    }
});