// Write your script here
// Write your script here
document.getElementById("contact-form").addEventListener("submit", async function(e) {
  e.preventDefault();

  const csrfToken = page_data.csrf_token;

  const name = document.querySelector('[name="name"]').value;
  const mobile = document.querySelector('[name="mobile"]').value;
  const subject = document.querySelector('[name="subject"]').value;
  const sender = document.querySelector('[name="email"]').value;
  const message = document.querySelector('[name="message"]').value;
    
const email_body = `Name: ${name}
Email: ${sender}
Mobile: ${mobile}

Message:
${message}`;

  const payload = {
    subject: subject,
    sender: sender,
    message: email_body
  };

  try {
    const response = await fetch('/api/method/frappe.www.contact.send_message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': csrfToken
      },
      body: JSON.stringify(payload)
    });

    const result = await response.json();

    if (response.status === 200) {
      Toastify({
        text: "📩 Message sent successfully!",
        close: true,
        gravity: "top",
        position: "center",
        stopOnFocus: true,
        style: {
          background: "var(--primary-color)",
        }
      }).showToast();
      e.target.reset();
    } else {
      Toastify({
        text: `❌ Failed to send message: ${result.message || 'Unknown error'}`,
        close: true,
        gravity: "top",
        position: "center",
        stopOnFocus: true,
        style: {
          background: "var(--primary-color-light)",
        }
      }).showToast();
    }
  } catch (error) {
    console.error("Contact form error:", error);
    Toastify({
      text: "⚠️ An error occurred. Please try again later.",
      close: true,
      gravity: "top",
      position: "center",
      stopOnFocus: true,
      style: {
        background: "var(--primary-color-light)",
      }
    }).showToast();
  }
});
