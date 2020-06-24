vcl 4.0;

backend default {
  .host = "tileserver:8000";
}

sub vcl_recv {
  if (req.url ~ "\.png$") {
    unset req.http.cookie;
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
