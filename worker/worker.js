export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+/g, '/');
    
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") return new Response(null, { headers: corsHeaders });

    const supabaseUrl = env.SUPABASE_URL;
    const serviceKey = env.SUPABASE_SERVICE_KEY;

    try {
      // 1. Log Event (Insert)
      if (path === "/log-event" && request.method === "POST") {
        const table = url.searchParams.get("table") || "exam_logs";
        const body = await request.json();

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
        const userId = url.searchParams.get("user_id");
        const program = url.searchParams.get("program");

        const res = await fetch(`${supabaseUrl}/rest/v1/exam_logs?user_id=eq.${userId}&program=eq.${program}&event_type=eq.finished&order=created_at.desc&select=*`, {
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
