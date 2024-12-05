// Run this code when the page loads
document.addEventListener("DOMContentLoaded", async () => {
  const newChatFlag = localStorage.getItem("new_chat_on_load");
  if (newChatFlag === "true") {
    localStorage.removeItem("new_chat_on_load"); // Remove the flag
    await createNewChat(); // Call createNewChat after the DOM is fully loaded
  } else {
    const recentId = localStorage.getItem("recent_id");
    if (recentId) {
      await loadChat(recentId); // Load the previous chat if recent_id is available
    } else {
      await createNewChat(); // Otherwise, create a new chat
    }
  }
});

/**
 * Simulates the typing effect for AI messages with markdown parsing and syntax highlighting.
 * @param {HTMLElement} aiMessageDiv - The div element that will contain the AI message.
 * @param {string} aiMessage - The AI response message.
 * @param {HTMLElement} conversationBox - The conversation box to scroll to the latest message.
 */
function streamer(aiMessageDiv, aiMessage, conversationBox) {
  let length = 0;
  const interval = setInterval(() => {
    aiMessageDiv.textContent += aiMessage[length++];
    if (length >= aiMessage.length) {
      clearInterval(interval);

      // After the typing effect is complete, parse and highlight the content
      let aiResponse = marked.parse(aiMessageDiv.textContent); // Markdown parsing
      let languageMatch = aiResponse.match(/```(\w+)/); // Regex to detect language
      if (languageMatch) {
        let language = languageMatch[1]; // Extract language (e.g., 'javascript')
        aiResponse = aiResponse.replace(
          /```(\w+)([\s\S]*?)```/g,
          `<pre><code class="language-$1">$2</code></pre>`
        );
      }

      aiMessageDiv.innerHTML = aiResponse; // Inject parsed response with markdown
      Prism.highlightAll(); // Apply syntax highlighting after the content is fully typed
    }
    conversationBox.scrollTop = conversationBox.scrollHeight;
  }, 0.001);
}

/**
 * Sends a message to the backend and updates the conversation with the response.
 * @async
 */
async function sendMessage() {
  let input = document.getElementById("messageInput");
  let message = input.value.trim();
  input.value = ""; // Clear the input
  let recentId = localStorage.getItem("recent_id"); // Retrieve `recent_id` from localStorage

  if (message !== "" && recentId !== null) {
    let conversationBox = document.getElementById("conversationBox");

    // Append user's message
    let userMessageDiv = document.createElement("div");
    userMessageDiv.classList.add(
      "message",
      "user-message",
      "bg-blue-500",
      "text-white-800",
      "p-3",
      "rounded-md",
      "mb-2",
      "max-w-xl",
      "break-all"
    );
    userMessageDiv.textContent = message; // Add the user's message
    let userParentDiv = document.createElement("div");
    userParentDiv.classList.add("flex", "items-end", "relative", "justify-end");
    userParentDiv.appendChild(userMessageDiv);
    conversationBox.appendChild(userParentDiv);
    conversationBox.scrollTop = conversationBox.scrollHeight;

    // Add loading animation for AI response
    let aiParentDiv = document.createElement("div");
    aiParentDiv.classList.add("flex", "items-start", "relative");
    let animationDiv = document.createElement("div");
    animationDiv.classList.add(
      "bg-white",
      "rounded-lg",
      "shadow-md",
      "p-4",
      "animate-pulse",
      "mb-2"
    );
    animationDiv.style.width = "80%"; // Set width of animation
    animationDiv.innerHTML = `
      <div class="w-2/3 h-4 bg-gray-700 rounded mb-2"></div>
      <div class="w-full h-8 bg-gray-700 rounded mb-2"></div>
      <div class="w-full h-8 bg-gray-700 rounded mb-2"></div>
      <div class="w-1/2 h-8 bg-gray-700 rounded"></div>
    `;
    aiParentDiv.appendChild(animationDiv);
    conversationBox.appendChild(aiParentDiv);
    conversationBox.scrollTop = conversationBox.scrollHeight;

    // Send the message to the backend
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message, recent_id: recentId }),
    });

    const data = await response.json();

    if (data.response) {
      // Remove animation before showing the AI response
      aiParentDiv.removeChild(animationDiv);

      // Create AI message div for the response
      let aiMessageDiv = document.createElement("div");
      aiMessageDiv.classList.add(
        "message",
        "ai-message",
        "bg-gray-700",
        "text-white",
        "p-3",
        "rounded-md",
        "mb-2",
        "max-w-xl",
        "break-all"
      );
      aiParentDiv.appendChild(aiMessageDiv);
      streamer(aiMessageDiv, data.response, conversationBox);

      // Update the chat title if it's the first user query
      const recentChatsList = document.querySelector(".recent-chats ul");
      const newChatItem = recentChatsList.querySelector(
        `li.chat-item[data-id='${recentId}']`
      );

      if (newChatItem && !newChatItem.dataset.titleSet) {
        const titleResponse = await fetch("/generate/title", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ response: data.response }),
        });
        const titleData = await titleResponse.json();

        if (titleData.success && titleData.title) {
          const is_saved = await fetch("/save/title", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              recent_id: recentId,
              chat_title: titleData.title,
            }),
          });
          const saved = await is_saved.json();
          if (saved.success) {
            const chatTitleSpan = newChatItem.querySelector("button.load-chat");
            chatTitleSpan.textContent = titleData.title; // Update the title
            newChatItem.dataset.titleSet = "true"; // Mark as title set
          }
        }
      }
    }
  }
}

/**
 * Loads a previous chat based on the `recent_id`.
 * @async
 * @param {string} recentId - The ID of the chat to load.
 */
async function loadChat(recentId) {
  console.log("Loading chat" + recentId);
  const response = await fetch(`/api/load_chat/${recentId}`);
  const data = await response.json();
  localStorage.setItem("recent_id", recentId);

  let conversationBox = document.getElementById("conversationBox");
  conversationBox.innerHTML = ""; // Clear current messages

  if (data.chat_history && data.chat_history.length > 0) {
    data.chat_history.forEach((chat) => {
      let messageDiv = document.createElement("div");
      messageDiv.classList.add(
        "message",
        chat.sender === "user" ? "user-message" : "ai-message",
        chat.sender === "user" ? "bg-blue-500" : "bg-gray-700",
        chat.sender === "user" ? "text-white-300" : "text-white-800",
        "p-3",
        "rounded-md",
        "mb-2",
        "max-w-xl",
        "break-all"
      );

      if (chat.sender === "user") {
        messageDiv.textContent = chat.message; // Plain text for user messages
      } else {
        // Handle AI response with syntax highlighting
        let aiResponse = marked.parse(chat.message); // Markdown parsing
        let languageMatch = aiResponse.match(/```(\w+)/); // Regex to detect language
        if (languageMatch) {
          let language = languageMatch[1]; // Extract language (e.g., 'javascript')
          aiResponse = aiResponse.replace(
            /```(\w+)([\s\S]*?)```/g,
            `<pre><code class="language-$1">$2</code></pre>`
          );
        }
        messageDiv.innerHTML = aiResponse; // Add AI's formatted response
      }

      let parentDiv = document.createElement("div");
      if (chat.sender === "user") {
        parentDiv.classList.add("flex", "items-end", "relative", "justify-end");
      } else {
        parentDiv.classList.add("flex", "items-start", "relative");
      }
      parentDiv.appendChild(messageDiv);
      conversationBox.appendChild(parentDiv);
    });

    // Automatically scroll to the latest message
    conversationBox.scrollTop = conversationBox.scrollHeight;

    // Apply syntax highlighting to all code blocks
    Prism.highlightAll();
  } else {
    let noMessagesDiv = document.createElement("div");
    noMessagesDiv.classList.add("message", "p-2", "rounded-md", "mb-2");
    noMessagesDiv.textContent = "Hey there, How can I help you today?";
    noMessagesDiv.classList.add(
      "flex",
      "flex-col",
      "items-center",
      "justify-center"
    );
    conversationBox.appendChild(noMessagesDiv);
  }
}

/**
 * Creates a new chat session.
 * Sends a request to create a new chat and initializes the conversation box.
 * @async
 */
async function createNewChat() {
  const conversationBox = document.getElementById("conversationBox");
  if (!conversationBox) {
    console.error(
      "Conversation box is not available. Ensure the page is fully loaded."
    );
    return;
  }

  try {
    const response = await fetch(`/api/new_recent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "New Chat" }), // Send the title in the request body
    });

    if (!response.ok) {
      console.error(
        "Failed to create a new chat session.",
        await response.text()
      );
      return;
    }

    const data = await response.json();

    if (data.success) {
      localStorage.setItem("recent_id", data.recent_id);
      console.log("Created new chat:", data.recent_id);
      startNewChat(data.recent_id);
    } else {
      console.error("Error:", data.error || "Unknown error occurred.");
    }
  } catch (error) {
    console.error(
      "An error occurred while creating a new chat session:",
      error
    );
  }
}

/**
 * Initializes the chat with a welcome message and updates the recent chats list.
 * @param {string} recent_id - The ID of the newly created chat session.
 */
function startNewChat(recent_id) {
  let conversationBox = document.getElementById("conversationBox");
  conversationBox.innerHTML = ""; // Clear conversation box

  // Add welcome message
  let welcomeMessageDiv = document.createElement("div");
  welcomeMessageDiv.classList.add(
    "message",
    "bg-gray-600",
    "p-2",
    "rounded-lg"
  );
  welcomeMessageDiv.textContent =
    "ChatBot: Hi there! How can I help you today?";
  conversationBox.appendChild(welcomeMessageDiv);

  let recentChatsList = document.getElementById("recentChatsList");

  // Create new <li> for the new chat
  let newChatItem = document.createElement("li");
  newChatItem.classList.add(
    "chat-item",
    "bg-gray-700",
    "p-2",
    "rounded-md",
    "flex",
    "items-center",
    "justify-between"
  );
  newChatItem.setAttribute("data-id", recent_id);

  // Create button to load the chat
  let loadChatButton = document.createElement("button");
  loadChatButton.type = "button";
  loadChatButton.classList.add(
    "load-chat",
    "flex-1",
    "text-left",
    "bg-transparent",
    "text-white",
    "font-medium",
    "hover:underline"
  );
  loadChatButton.textContent = "New Chat"; // Set default chat title
  loadChatButton.setAttribute("onclick", `loadChat('${recent_id}')`);

  // Create button to delete the chat
  let deleteChatButton = document.createElement("button");
  deleteChatButton.type = "button";
  deleteChatButton.classList.add(
    "delete-chat",
    "bg-red-600",
    "hover:bg-red-800",
    "text-white",
    "p-2",
    "rounded-full",
    "ml-2"
  );
  deleteChatButton.setAttribute("aria-label", "Close");
  deleteChatButton.setAttribute(
    "onclick",
    `deleteChat(event, '${recent_id}', this)`
  );
  deleteChatButton.innerHTML = "&times;"; // Add 'x' character for close button

  // Append buttons to the new chat item
  newChatItem.appendChild(loadChatButton);
  newChatItem.appendChild(deleteChatButton);

  // Insert the new chat item at the top of the list
  recentChatsList.insertBefore(newChatItem, recentChatsList.firstChild);
}

/**
 * Handles the login process with email and password.
 * @async
 * @param {Event} event - The submit event from the login form.
 */
async function login(event) {
  event.preventDefault();

  let email = document.getElementById("email").value;
  let password = document.getElementById("password").value;

  const response = await fetch("/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: email, password: password }),
  });
  const data = await response.json();

  if (data.success) {
    localStorage.setItem("new_chat_on_load", "true"); // Set a flag to initialize new chat
    window.location.href = "/chat"; // Redirect to the chat page
  } else {
    window.location.href = "/login"; // Redirect to the login page
  }
}

/**
 * Redirects the user to Google login.
 * @param {Event} event - The submit event from the Google login button.
 */
function loginWithGoogle(event) {
  event.preventDefault();
  window.location.href = "/login/google";
}

/**
 * Handles the search functionality for filtering recent chats.
 * @listens input#searchInput
 */
document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("searchInput");
  const recentChatsList = document.getElementById("recentChatsList");

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      const filterText = searchInput.value.toLowerCase();
      const chatItems = recentChatsList.querySelectorAll(".chat-item");

      chatItems.forEach((chatItem) => {
        const chatName = chatItem.textContent.toLowerCase();
        if (chatName.includes(filterText)) {
          chatItem.style.display = "";
        } else {
          chatItem.style.display = "none";
        }
      });
    });
  }
});

/**
 * Deletes a chat session.
 * @async
 * @param {Event} event - The click event on the delete button.
 * @param {string} recentId - The ID of the chat to be deleted.
 * @param {HTMLElement} buttonElement - The delete button element.
 */
async function deleteChat(event, recentId, buttonElement) {
  event.stopPropagation();
  try {
    const response = await fetch(`/api/delete_chat/${recentId}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
    });

    const data = await response.json();

    if (data.success) {
      console.log("deleted");
      // Remove the parent <li> from the DOM
      const listItem = buttonElement.closest("li");
      const currentId = localStorage.getItem("recent_id");
      listItem.remove();

      if (currentId === recentId) {
        const firstChatItem = document.querySelector(
          "#recentChatsList .chat-item"
        );
        if (firstChatItem) {
          const onclickAttr = firstChatItem.getAttribute("onclick");
          if (onclickAttr) {
            const match = onclickAttr.match(/loadChat\('(.+?)'\)/);
            if (match && match[1]) {
              const firstChatId = match[1];
              localStorage.setItem("recent_id", firstChatId); // Update recent_id
              loadChat(firstChatId); // Load the first chat
            }
          }
        } else {
          createNewChat(); // No chats left; create a new chat
        }
      } else {
        loadChat(currentId); // If not current chat, load it again
      }

      showFlashMessage(data.message, "success", 3000);
    } else {
      showFlashMessage(data.message, "error", 3000);
    }
  } catch (error) {
    console.error("An error occurred while deleting the chat:", error);
    showFlashMessage("An error occurred. Please try again.", "error");
  }
}

/**
 * Displays a flash message on the screen.
 * @param {string} message - The message to be displayed.
 * @param {string} type - The type of message ("success" or "error").
 * @param {number} time - The duration to display the message (in milliseconds).
 */
function showFlashMessage(message, type, time) {
  let flashContainer = document.getElementById("flash-container");
  if (!flashContainer) {
    flashContainer = document.createElement("div");
    flashContainer.id = "flash-container";
    flashContainer.style.position = "fixed";
    flashContainer.style.top = "10px";
    flashContainer.style.right = "10px";
    flashContainer.style.zIndex = "9999";
    document.body.appendChild(flashContainer);
  }

  const flashMessage = document.createElement("div");
  flashMessage.textContent = message;
  flashMessage.style.padding = "10px 20px";
  flashMessage.style.borderRadius = "5px";
  flashMessage.style.marginBottom = "10px";
  flashMessage.style.color = "#fff";
  flashMessage.style.fontWeight = "bold";

  // Set the background color based on message type
  if (type === "success") {
    flashMessage.style.backgroundColor = "green";
  } else if (type === "error") {
    flashMessage.style.backgroundColor = "red";
  }

  flashContainer.appendChild(flashMessage);
  setTimeout(() => flashMessage.remove(), time); // Remove after specified time
}
