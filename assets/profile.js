const API_URL = "https://algocare-api.abdul01abdul03.workers.dev";
const SUPABASE_URL = "https://uhrjtcocwejddtzyjyhr.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_C_i1zk4P2phfIALmI6C7Iw_pYSMTGfQ";

document.addEventListener("DOMContentLoaded", async () => {
  const session = getSession();
  if (!session) { window.location.href = "/login"; return; }

  const user = session.user;
  const name = user.user_metadata?.name || user.email.split('@')[0];
  const bio = user.user_metadata?.bio || "";
  let avatarUrl = user.user_metadata?.avatar_url || null;

  // Populate fields
  document.getElementById("profileName").value = name;
  document.getElementById("profileBio").value = bio;
  
  const preview = document.getElementById("avatarPreview");
  if (avatarUrl) {
    preview.innerHTML = `<img src="${avatarUrl}" style="width:100%; height:100%; object-fit:cover;">`;
  } else {
    preview.textContent = name.charAt(0).toUpperCase();
  }

  // Handle Avatar Upload
  document.getElementById("avatarInput").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Show loading state
    const label = document.querySelector('label[for="avatarInput"]');
    const originalText = label.textContent;
    label.textContent = "Uploading...";

    try {
      // Upload to Supabase Storage directly
      const fileExt = file.name.split('.').pop();
      const fileName = `${user.id}/avatar_${Date.now()}.${fileExt}`;
      
      const res = await fetch(`${SUPABASE_URL}/storage/v1/object/avatars/${fileName}`, {
        method: "POST",
        headers: { 
          "apikey": SUPABASE_ANON_KEY, 
          "Authorization": `Bearer ${session.access_token}` 
        },
        body: file
      });

      if (!res.ok) throw new Error("Upload failed");
      
      // Get public URL
      avatarUrl = `${SUPABASE_URL}/storage/v1/object/public/avatars/${fileName}`;
      preview.innerHTML = `<img src="${avatarUrl}" style="width:100%; height:100%; object-fit:cover;">`;
      
    } catch (err) {
      alert("Error uploading image: " + err.message);
    } finally {
      label.textContent = originalText;
    }
  });

  // Handle Save Profile
  document.getElementById("profileForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("saveBtn");
    const newBio = document.getElementById("profileBio").value;

    btn.disabled = true;
    btn.textContent = "Saving...";

    try {
      const res = await fetchWithAuth(`${API_URL}/update-profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bio: newBio, avatar_url: avatarUrl })
      });

      if (!res.ok) throw new Error("Failed to save profile");

      // Update local session so topbar updates instantly without re-logging
      const currentSession = getSession();
      if (currentSession && currentSession.user) {
        currentSession.user.user_metadata.bio = newBio;
        currentSession.user.user_metadata.avatar_url = avatarUrl;
        localStorage.setItem("algocare_session", JSON.stringify(currentSession));
      }

      alert("Profile saved successfully!");
      window.location.href = "/dashboard";
    } catch (err) {
      alert("Error: " + err.message);
      btn.disabled = false;
      btn.textContent = "Save Changes";
    }
  });
});
