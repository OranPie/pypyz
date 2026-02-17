def on_startup(context, api):
    api.emit_event("startup.loaded", {"tick": context.tick, "phase": context.payload.get("phase")})
