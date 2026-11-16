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

    // --- 🛡️ RATE LIMITING LOGIC ---
    const ip = request.headers.get("CF-Connecting-IP") || "unknown-ip";
    const minuteWindow = Math.floor(Date.now() / 60000); // Current minute
    const kvKey = `rate:${ip}:${minuteWindow}`;
    
    try {
      // Get the current request count for this IP in this minute
      const currentCountStr = await env.RATE_LIMIT_KV.get(kvKey);
      const currentCount = parseInt(currentCountStr || "0", 10);

      if (currentCount >= 60) {
        return new Response(JSON.stringify({ error: "Too many requests. Please wait a minute." }), { 
          status: 429, 
          headers: { ...corsHeaders, "Content-Type": "application/json" } 
        });
      }

      // Increment the count (expires after 60 seconds automatically)
      await env.RATE_LIMIT_KV.put(kvKey, (currentCount + 1).toString(), { expirationTtl: 65 });
    } catch (e) {
      console.warn("Rate limit KV error:", e);
      // If KV fails, we let the request through rather than breaking the app
    }
    // ------------------------------

    const supabaseUrl = env.SUPABASE_URL;
    const serviceKey = env.SUPABASE_SERVICE_KEY;

    try {
      // --- SECURITY GUARD: Verify User Token ---
      const authHeader = request.headers.get("Authorization");
      if (!authHeader || !authHeader.startsWith("Bearer ")) {
        return new Response(JSON.stringify({ error: "Unauthorized: Missing Token" }), { status: 401, headers: corsHeaders });
      }

      const token = authHeader.replace("Bearer ", "");
      
      const userRes = await fetch(`${supabaseUrl}/auth/v1/user`, {
        headers: { "apikey": serviceKey, "Authorization": `Bearer ${token}` }
      });
      
      if (!userRes.ok) {
        return new Response(JSON.stringify({ error: "Unauthorized: Invalid Token" }), { status: 401, headers: corsHeaders });
      }
      
      const user = await userRes.json();

      // 1. Log Event (Insert)
      if (path === "/log-event" && request.method === "POST") {
        const table = url.searchParams.get("table") || "exam_logs";
        const body = await request.json();
        
        body.user_id = user.id;

        const res = await fetch(`${supabaseUrl}/rest/v1/${table}`, {
          method: "POST",
          headers: { "apikey": serviceKey, "Authorization": `Bearer ${serviceKey}`, "Content-Type": "application/json", "Prefer": "return=minimal" },
          body: JSON.stringify(body)
        });

        if (!res.ok) return new Response(await res.text(), { status: 400, headers: corsHeaders });
        return new Response(JSON.stringify({ success: true }), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
      }

      // 2. Get Stats (Dashboard)
      if (path === "/get-stats" && request.method === "GET") {
        const program = url.searchParams.get("program");

        const res = await fetch(`${supabaseUrl}/rest/v1/exam_logs?user_id=eq.${user.id}&program=eq.${program}&event_type=eq.finished&order=created_at.desc&select=*`, {
          headers: { "apikey": serviceKey, "Authorization": `Bearer ${serviceKey}` }
        });

        if (!res.ok) throw new Error(await res.text());
        return new Response(await res.text(), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
      }

      // 3. Leaderboard (RPC)
      if (path === "/leaderboard" && request.method === "GET") {
        const program = url.searchParams.get("program");
        const mode = url.searchParams.get("mode");

        const res = await fetch(`${supabaseUrl}/rest/v1/rpc/get_leaderboard`, {
          method: "POST",
          headers: { "apikey": serviceKey, "Authorization": `Bearer ${serviceKey}`, "Content-Type": "application/json" },
          body: JSON.stringify({ prog: program, test_mode: mode, limit_count: 20 })
        });

        if (!res.ok) throw new Error(await res.text());
        return new Response(await res.text(), { headers: { ...corsHeaders, "Content-Type": "application/json" } });
      }

    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } });
    }
    return new Response(`Not Found: ${path}`, { status: 404, headers: corsHeaders });
  }
};
