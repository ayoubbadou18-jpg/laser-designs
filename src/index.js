export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Serve objects: /obj/<path>
    if (url.pathname.startsWith("/obj/")) {
      const key = decodeURIComponent(url.pathname.slice("/obj/".length));
      const obj = await env.BUCKET.get(key);
      if (!obj) return new Response("Not found", { status: 404 });

      const headers = new Headers();
      obj.writeHttpMetadata(headers);
      headers.set("cache-control", "public, max-age=31536000, immutable");
      return new Response(obj.body, { headers });
    }

    // JSON list: /api/list
    if (url.pathname === "/api/list") {
      const imgListed = await env.BUCKET.list({ prefix: "images/" });
      const fileListed = await env.BUCKET.list({ prefix: "files/" });

      const baseName = (key) => {
        const name = key.split("/").pop();
        const dot = name.lastIndexOf(".");
        return dot >= 0 ? name.slice(0, dot) : name;
      };

      const imgs = new Map();
      for (const o of imgListed.objects) imgs.set(baseName(o.key), o.key);

      const files = new Map();
      for (const o of fileListed.objects) files.set(baseName(o.key), o.key);

      const names = new Set([...imgs.keys(), ...files.keys()]);
      const origin = `${url.protocol}//${url.host}`;

      const items = [...names].sort().map((id) => ({
        id,
        imageUrl: imgs.get(id) ? `${origin}/obj/${encodeURIComponent(imgs.get(id))}` : null,
        fileUrl: files.get(id) ? `${origin}/obj/${encodeURIComponent(files.get(id))}` : null,
      }));

      return Response.json({ items });
    }

    return new Response("Use /api/list or /obj/<key>", { status: 200 });
  },
};
