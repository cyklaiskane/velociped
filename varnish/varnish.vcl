vcl 4.0;

backend default none;

backend tileserver {
  .host = "tileserver";
  .port = "8000";
}

backend mapproxy {
  .host = "mapproxy";
  .port = "8000";
}

sub vcl_recv {
  if (req.url ~ "/\d+/\d+/\d+\.png$") {
    unset req.http.cookie;
  } else {
    return (synth(404, "Not found"));
  }

  if (req.url ~ "^/nedtonad") {
    set req.backend_hint = mapproxy;
    set req.url = regsub(req.url, ".*/(\d+/\d+/\d+\.png)$", "/tiles/1.0.0/nedtonad/webmercator/\1");
  } elif (req.url ~ "^/trafiksakerhet") {
    set req.backend_hint = tileserver;
    set req.url = regsub(req.url, ".*/(\d+/\d+/\d+\.png)$", "/styles/trafiksakerhet/\1");
  } else {
    return (synth(404, "Not found"));
  }
}

sub vcl_backend_response {
  if (beresp.status < 300 && bereq.url ~ "\.png$") {
    set beresp.ttl = 1d;
  }
}

sub vcl_deliver {
  if (obj.hits > 0) { # Add debug header to see if it's a HIT/MISS and the number of hits, disable when not needed
    set resp.http.X-Cache = "HIT";
  } else {
    set resp.http.X-Cache = "MISS";
  }
  return (deliver);
}
