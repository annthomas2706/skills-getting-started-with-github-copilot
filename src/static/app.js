document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        const participantsList = details.participants
          .map(participant => `<li>${participant}</li>`)
          .join('');
        
        const participantsDropdown = details.participants
          .map(participant => `<option value="${participant}">${participant}</option>`)
          .join('');

        let removeSection = '';
        if (details.participants.length > 0) {
          removeSection = `
            <div class="remove-participant-section">
              <label for="remove-${name}">Remove Participant:</label>
              <div class="remove-controls">
                <select id="remove-${name}" class="participant-select" data-activity="${name}">
                  <option value="">-- Select participant --</option>
                  ${participantsDropdown}
                </select>
                <button class="remove-participant-btn" data-activity="${name}">Delete</button>
              </div>
            </div>
          `;
        }

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <strong>Current Participants:</strong>
            <ul class="participants-list">
              ${participantsList}
            </ul>
            ${removeSection}
          </div>
        `;

        activitiesList.appendChild(activityCard);
        
        // Add event listener for delete button
        if (details.participants.length > 0) {
          const deleteBtn = activityCard.querySelector('.remove-participant-btn');
          const select = activityCard.querySelector('.participant-select');
          
          deleteBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const email = select.value;
            
            if (!email) {
              messageDiv.textContent = 'Please select a participant to delete';
              messageDiv.className = 'error';
              messageDiv.classList.remove('hidden');
              return;
            }
            
            const activity = deleteBtn.dataset.activity;
            
            try {
              const response = await fetch(
                `/activities/${encodeURIComponent(activity)}/participants/${encodeURIComponent(email)}`,
                { method: 'DELETE' }
              );
              
              if (response.ok) {
                fetchActivities();
                messageDiv.textContent = `Removed ${email} from ${activity}`;
                messageDiv.className = 'success';
                messageDiv.classList.remove('hidden');
                setTimeout(() => {
                  messageDiv.classList.add('hidden');
                }, 5000);
              } else {
                const result = await response.json();
                messageDiv.textContent = result.detail || 'Failed to remove participant';
                messageDiv.className = 'error';
                messageDiv.classList.remove('hidden');
              }
            } catch (error) {
              messageDiv.textContent = 'Failed to remove participant';
              messageDiv.className = 'error';
              messageDiv.classList.remove('hidden');
              console.error('Error removing participant:', error);
            }
          });
        }

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
