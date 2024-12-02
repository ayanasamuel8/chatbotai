// Run this code when the page loads
document.addEventListener("DOMContentLoaded", async () => {
  const newChatFlag = localStorage.getItem("new_chat_on_load");
  if (newChatFlag === "true") {
    localStorage.removeItem("new_chat_on_load"); // Remove the flag
    await createNewChat(); // Safely call createNewChat after the DOM is fully loaded
  } else {
    const recentId = localStorage.getItem("recent_id");
    if (recentId) {
      await loadChat(recentId);
    } else {
      await createNewChat();
    }
  }
});

// Function to send a message
// Function to send a message
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
      "p-2",
      "rounded-md",
      "mb-2",
      "break-word",
      "break-all"
    );
    userMessageDiv.textContent = message; // Add the user's message
    let userParentDiv = document.createElement("div");
    userParentDiv.classList.add(
      "flex",
      "flex-col",
      "items-end",
      "relative",
      "justify-end"
    );
    userParentDiv.appendChild(userMessageDiv);
    conversationBox.appendChild(userParentDiv);

    // Send to backend
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message, recent_id: recentId }),
    });

    const data = await response.json();
    if (data.response) {
      let aiMessageDiv = document.createElement("div");
      aiMessageDiv.classList.add(
        "message",
        "ai-message",
        "bg-gray-700",
        "text-white-800",
        "p-2",
        "rounded-md",
        "mb-2",
        "break-word",
        "break-all"
      );

      // Detect language and wrap code blocks
      let aiResponse = marked.parse(data.response); // Markdown parsing
      let languageMatch = aiResponse.match(/```(\w+)/); // Regex to detect language
      if (languageMatch) {
        let language = languageMatch[1]; // Extract language (e.g., 'javascript')
        aiResponse = aiResponse.replace(
          /```(\w+)([\s\S]*?)```/g,
          `<pre><code class="language-$1">$2</code></pre>`
        );
      }

      aiMessageDiv.innerHTML = aiResponse; // Inject parsed response
      let aiParentDiv = document.createElement("div");
      aiParentDiv.classList.add("flex", "items-start", "relative");
      aiParentDiv.appendChild(aiMessageDiv);
      conversationBox.appendChild(aiParentDiv);
      conversationBox.scrollTop = conversationBox.scrollHeight;

      // Re-run Prism.js for syntax highlighting
      Prism.highlightAll();

      // Update the chat title if it's the first user query
      const recentChatsList = document.querySelector(".recent-chats ul");
      const newChatItem = recentChatsList.querySelector(
        `li.chat-item:last-child`
      );

      if (newChatItem && !newChatItem.dataset.titleSet) {
        // Request title generation from the backend
        const titleResponse = await fetch("/generate/title", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ response: data.response }),
        });
        const titleData = await titleResponse.json();

        if (titleData.success && titleData.title) {
          console.log(titleData.title);
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
            newChatItem.textContent = titleData.title; // Update the title
            newChatItem.dataset.titleSet = "true"; // Mark as title set
          }
        }
      }
    }
  }
}

// Function to load a previous chat
async function loadChat(recentId) {
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
        "p-2",
        "rounded-md",
        "mb-2",
        "break-word",
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
      "relative",
      "justify-center"
    );
    conversationBox.appendChild(noMessagesDiv);
  }
}

// Function to create a new chat
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
      headers: {
        "Content-Type": "application/json",
      },
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

// Function to start a new chat
function startNewChat(recent_id) {
  let conversationBox = document.getElementById("conversationBox");
  conversationBox.innerHTML = ""; // Clear conversation box

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
  let recentChatsList = document.querySelector(".recent-chats ul");

  let newChatItem = document.createElement("li");
  newChatItem.classList.add(
    "chat-item",
    "bg-gray-600",
    "p-2",
    "rounded-md",
    "hover:bg-blue-500",
    "cursor-pointer"
  );
  newChatItem.textContent = "New Chat"; // Set a unique chat name
  newChatItem.onclick = function () {
    loadChat(recent_id); // Attach an event handler to load the chat
  };
  recentChatsList.appendChild(newChatItem);
}

// Login function
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
  } else window.location.href = "/login"; // Redirect to the login page
}

function loginWithGoogle(event) {
  event.preventDefault();
  window.location.href = "/login/google";
}

// Function to handle search input
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

/*
function toggleRecentChats() {
  const sidebar = document.getElementById("recentChatsSidebar");
  if (sidebar.style.width === "0px" || sidebar.classList.contains("hidden")) {
    sidebar.style.width = "16rem";
    sidebar.classList.remove("hidden");
  } else {
    sidebar.style.width = "0";
    setTimeout(() => sidebar.classList.add("hidden"), 300);
  }
}

// Ensure recent chats are scrollable
window.addEventListener("resize", () => {
  const sidebar = document.getElementById("recentChatsSidebar");
  if (window.innerWidth < 768) {
    sidebar.style.width = "0";
    sidebar.classList.add("hidden");
  } else {
    sidebar.style.width = "16rem";
    sidebar.classList.remove("hidden");
  }
});
*/
