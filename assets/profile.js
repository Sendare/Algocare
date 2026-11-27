const API_URL = "https://algocare-api.abdul01abdul03.workers.dev";
const SUPABASE_URL = "https://uhrjtcocwejddtzyjyhr.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_C_i1zk4P2phfIALmI6C7Iw_pYSMTGfQ";

let currentAvatarUrl = null;

document.addEventListener("DOMContentLoaded", () => {
  const session = getSession();
  if (!session) { window.location.href = "/login"; return; }

  const user = session.user;
  const meta = user.user_metadata || {};
  
  // Pre-fill fields
  document.getElementById("profileName").value = meta.name || "";
  document.getElementById("profileUsername").value = meta.username || "";
  document.getElementById("profileAge").value = meta.age || "";
  document.getElementById("profileGender").value = meta.gender || "";
  document.getElementById("profileBio").value = meta.bio || "";
  
  currentAvatarUrl = meta.avatar_url || null;
  const preview = document.getElementById("avatarPreview");
  
  if (currentAvatarUrl) {
    preview.innerHTML = `<img src="${currentAvatarUrl}" style="width:100%; height:100%; object-fit:cover;">`;
  } else {
    preview.textContent = (meta.name || user.email).charAt(0).toUpperCase();
  }

  // Attach upload listener
  const avatarInput = document.getElementById("avatarInput");
  avatarInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const label = document.getElementById("uploadLabel");
    const originalText = label.textContent;
    label.textContent = "Uploading...";

    try {
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

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Status ${res.status}: ${errorText}`);
      }
      
      currentAvatarUrl = `${SUPABASE_URL}/storage/v1/object/public/avatars/${fileName}`;
      preview.innerHTML = `<img src="${currentAvatarUrl}" style="width:100%; height:100%; object-fit:cover;">`;
      alert("Photo uploaded! Click 'Save Changes' to apply.");
      
    } catch (err) {
      alert("UPLOAD ERROR: " + err.message);
    } finally {
      label.textContent = originalText;
    }
  });
});

// Global function called by the button
window.saveProfileData = async function() {
  const session = getSession();
  if (!session) return;

  const btn = document.getElementById("saveBtn");
  btn.disabled = true;
  btn.textContent = "Saving...";

  const updatedData = {
    name: document.getElementById("profileName").value,
    username: document.getElementById("profileUsername").value,
    age: document.getElementById("profileAge").value,
    gender: document.getElementById("profileGender").value,
    bio: document.getElementById("profileBio").value,
    avatar_url: currentAvatarUrl
  };

  try {
    const res = await fetch(`${API_URL}/update-profile`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${session.access_token}`
      },
      body: JSON.stringify(updatedData)
    });

    if (!res.ok) throw new Error(await res.text());
    const result = await res.json();

    // Update local session
    const currentSession = getSession();
    if (currentSession && currentSession.user) {
      currentSession.user.user_metadata = result.user.user_metadata;
      localStorage.setItem("algocare_session", JSON.stringify(currentSession));
    }

    alert("Profile saved successfully!");
    window.location.href = "/dashboard";
  } catch (err) {
    alert("SAVE ERROR: " + err.message);
    btn.disabled = false;
    btn.textContent = "Save Changes";
  }
};
