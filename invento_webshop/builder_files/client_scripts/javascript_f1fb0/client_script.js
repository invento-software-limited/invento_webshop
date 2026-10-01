// Write your script here
document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const activeTopic = params.get("topic");

  if (!activeTopic) return;

  const topicLinks = document.querySelectorAll(
    'a[href^="/help-advice?topic="]'
  );

  topicLinks.forEach(link => {
    const linkTopic = decodeURIComponent(
      new URL(link.href).searchParams.get("topic")
    );

    if (linkTopic === activeTopic) {
      link.classList.add("is-active");
    } else {
      link.classList.remove("is-active");
    }
  });
});

const searchInput = document.querySelector('input[name="faq-search"]');
console.log(searchInput)
if (searchInput) {
  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();

      const value = e.target.value.trim();
      const params = new URLSearchParams(window.location.search);

      if (value) {
        params.set("search", value);
      } else {
        params.delete("search");
      }

      window.location.search = params.toString();
    }
  });
}

document.getElementById("faq-search").addEventListener("click", () => {
  const value = searchInput.value.trim();
  const params = new URLSearchParams(window.location.search);

  if (value) {
    params.set("search", value);
  } else {
    params.delete("search");
  }

  window.location.search = params.toString();
});
