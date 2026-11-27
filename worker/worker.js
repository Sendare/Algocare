export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+/g, '/');
    
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    };

    if (request.method === "OPTIONS") return new Response(null, { headers: corsHeaders });

    // --- 🛡️ RATE LIMITING ---
    const ip = request.headers.get("CF-Connecting-IP") || "unknown-ip";
    const minuteWindow = Math.floor(Date.now() / 60000);
    const kvKey = `rate:${ip}:${minuteWindow}`;
    
    try {
      const currentCountStr = await env.RATE_LIMIT_KV.get(kvKey);
      const currentCount = parseInt(currentCountStr || "0", 10);
      if (currentCount >= 60) {
        return new Response(JSON.stringify({ error: "Too many requests." }), { status: 429, headers: corsHeaders });
      }
      await env.RATE_LIMIT_KV.put(kvKey, (currentCount + 1).toString(), { expirationTtl: 65 });
    } catch (e) {}

    const supabaseUrl = env.SUPABASE_URL;
    const serviceKey = env.SUPABASE_SERVICE_KEY;

    try {
      // --- SECURITY GUARD ---
      const authHeader = request.headers.get("Authorization");
      if (!authHeader || !authHeader.startsWith("Bearer ")) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401, headers: corsHeaders });
      }

      const token = authHeader.replace("Bearer ", "");
      const userRes = await fetch(`${supabaseUrl}/auth/v1/user`, {
        headers: { "apikey": serviceKey, "Authorization": `Bearer ${token}` }
      });
      
      if (!userRes.ok) return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401, headers: corsHeaders });
      const user = await userRes.json();

      // --- UPDATE PROFILE ENDPOINT ---
      if (path === "/update-profile" && request.method === "POST") {
        const b = await request.json();
        
        // Sanitize and validate inputs
        const avatar = typeof b.avatar_url === "string" &&
          b.avatar_url.startsWith(`${supabaseUrl}/storage/v1/object/public/avatars/`)
          ? b.avatar_url : (user.user_metadata?.avatar_url || null);

        const meta = {
          ...(user.user_metadata || {}),
          name: String(b.name || "").slice(0, 80),
          username: String(b.username || "").slice(0, 30),
          age: String(b.age || "").slice(0, 3),
          gender: ["Male", "Female", "Other"].includes(b.gender) ? b.gender : "",
          school: String(b.school || "").slice(0, 100),
          bio: String(b.bio || "").slice(0, 300),
          school: String(b.school || "").slice(0, 100),
          avatar_url: avatar
        };

        const r = await fetch(`${supabaseUrl}/auth/v1/admin/users/${user.id}`, {
          method: "PUT",
          headers: { "apikey": serviceKey, "Authorization": `Bearer ${serviceKey}`, "Content-Type": "application/json" },
          body: JSON.stringify({ user_metadata: meta })
        });
        
        if (!r.ok) return new Response(await r.text(), { status: 400, headers: corsHeaders });
        const updated = await r.json();
        return new Response(JSON.stringify({ user: updated }), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
      }

      // --- ADMIN ENDPOINT ---
      if (path === "/admin-data" && request.method === "GET") {
        // STRICT ADMIN CHECK
        if (user.email !== "abdul01abdul03@gmail.com") {
          return new Response(JSON.stringify({ error: "Forbidden: Admin access only" }), { status: 403, headers: corsHeaders });
        }

        // 1. Fetch Users from Supabase Admin API
        const usersRes = await fetch(`${supabaseUrl}/auth/v1/admin/users`, {
          headers: { "apikey": serviceKey, "Authorization": `Bearer ${serviceKey}` }
        });
        const usersData = await usersRes.json();
        const users = usersData.users ? usersData.users.map(u => ({
            id: u.id,
            email: u.email,
            name: u.user_metadata?.name || "N/A",
            school: u.user_metadata?.school || "N/A",
            joined: u.created_at
        })) : [];

        // 2. Fetch Feedback
        const fbRes = await fetch(`${supabaseUrl}/rest/v1/feedback?order=created_at.desc&limit=30`, {
          headers: { "apikey": serviceKey, "Authorization": `Bearer ${serviceKey}` }
        });
        const feedback = await fbRes.json();

        // 3. Fetch Recent Logs
        const logRes = await fetch(`${supabaseUrl}/rest/v1/exam_logs?event_type=eq.finished&order=created_at.desc&limit=30`, {
          headers: { "apikey": serviceKey, "Authorization": `Bearer ${serviceKey}` }
        });
        const logs = await logRes.json();

        // 4. Fetch Article Events
        const artRes = await fetch(`${supabaseUrl}/rest/v1/article_events?order=created_at.desc&limit=30`, {
          headers: { "apikey": serviceKey, "Authorization": `Bearer ${serviceKey}` }
        });
        const articles = await artRes.json();

        return new Response(JSON.stringify({ users, feedback, logs, articles }), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
      }

      // 1. Log Event (Whitelisted)
      if (path === "/log-event" && request.method === "POST") {
        const table = url.searchParams.get("table");
        const TABLES = {
          exam_logs: ["attempt_id","program","event_type","test_type","test_identifier","question_count","attempted","correct"],
          feedback: ["program","test_type","stars","comment"],
          article_events: ["program","topic_id","event_type"]
        };
        
        if (!TABLES[table]) {
          return new Response(JSON.stringify({ error: "Invalid table" }), { status: 400, headers: corsHeaders });
        }

        const raw = await request.json();
        const row = {};
        for (const k of TABLES[table]) {
          if (k in raw) row[k] = raw[k];
        }

        // Validate program
        if (!["nursing", "midwifery"].includes(row.program)) {
          return new Response(JSON.stringify({ error: "Invalid program" }), { status: 400, headers: corsHeaders });
        }

        // Override user data securely
        row.user_id = user.id;
        row.user_name = String(user.user_metadata?.username || user.user_metadata?.name || "Student").slice(0, 30);

        // Sanitize specific tables
        if (table === "feedback") {
          row.stars = Math.min(5, Math.max(1, parseInt(row.stars) || 1));
          row.comment = String(row.comment || "").slice(0, 500);
        }

        // Validate scores
        if (table === "exam_logs" && row.event_type === "finished") {
          const c = parseInt(row.correct), a = parseInt(row.attempted), n = parseInt(row.question_count);
          if (!(0 <= c && c <= a && a <= n && n <= 250)) {
            return new Response(JSON.stringify({ error: "Invalid score data" }), { status: 400, headers: corsHeaders });
          }
        }

        const res = await fetch(`${supabaseUrl}/rest/v1/${table}`, {
          method: "POST",
          headers: { "apikey": serviceKey, "Authorization": `Bearer ${serviceKey}`, "Content-Type": "application/json", "Prefer": "return=minimal" },
          body: JSON.stringify(row)
        });
        
        if (!res.ok) return new Response(await res.text(), { status: 400, headers: corsHeaders });
        return new Response(JSON.stringify({ success: true }), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
      }

      // 2. Get Stats
      if (path === "/get-stats" && request.method === "GET") {
        const program = url.searchParams.get("program");
        if (!["nursing", "midwifery"].includes(program)) {
          return new Response(JSON.stringify({ error: "Invalid program" }), { status: 400, headers: corsHeaders });
        }
        const safeProgram = encodeURIComponent(program);
        const res = await fetch(`${supabaseUrl}/rest/v1/exam_logs?user_id=eq.${user.id}&program=eq.${safeProgram}&event_type=eq.finished&order=created_at.desc&select=*`, {
          headers: { "apikey": serviceKey, "Authorization": `Bearer ${serviceKey}` }
        });
        if (!res.ok) throw new Error(await res.text());
        return new Response(await res.text(), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
      }

      // 3. Leaderboard
      if (path === "/leaderboard" && request.method === "GET") {
        const program = url.searchParams.get("program");
        const mode = url.searchParams.get("mode");
        if (!["nursing", "midwifery"].includes(program) || !["real_feel", "practice"].includes(mode)) {
          return new Response(JSON.stringify({ error: "Invalid params" }), { status: 400, headers: corsHeaders });
        }
        const res = await fetch(`${supabaseUrl}/rest/v1/rpc/get_leaderboard`, {
          method: "POST",
          headers: { "apikey": serviceKey, "Authorization": `Bearer ${serviceKey}`, "Content-Type": "application/json" },
          body: JSON.stringify({ prog: program, test_mode: mode, limit_count: 20 })
        });
        if (!res.ok) throw new Error(await res.text());
        return new Response(await res.text(), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
      }

    } catch (err) {
      console.error(err); return new Response(JSON.stringify({ error: "Internal Server Error" }), { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } });
    }
    return new Response(`Not Found: ${path}`, { status: 404, headers: corsHeaders });
  }
};
