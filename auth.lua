-- Registro de la acción "api_auth" para usar en el flujo http-req
core.register_action("api_auth", { "http-req" }, function(txn)
    local auth_url = os.getenv("AUTH_SERVICE_URL") or "http://mi_auth_service:5000"
    local verify_endpoint = auth_url .. "/auth/verify"

    core.log(core.notice, "AUTH:" .. verify_endpoint)

    -- 1. Intentar obtener la cookie de sesión
    local session_id = txn.f:cookie("ions_proxy_id")

    -- Si no hay cookie, marcamos como no autenticado y salimos rápido
    if not session_id or session_id == "" then
        txn.set_var(txn, "txn.authenticated", false)
        return
    end

    -- 2. Configurar el cliente HTTP nativo de HAProxy
    local httpcli = core.httpclient()

    -- 3. Llamada a la API de verificación
    -- Usamos el nombre del servicio 'mi_auth_service' definido en docker-compose
    local response = httpcli:get {
        url = verify_endpoint,
        headers = {
            ["cookie"] = { "ions_proxy_id=" .. session_id },
            ["x-host"] = { txn.f:hdr("host") },
            ["x-real-ip"] = { txn.f:hdr("x-real-ip") }
        },
        timeout = 1000 -- 1 segundo de timeout máximo
    }

    -- 4. Procesar la respuesta de la API
    -- Tu FastAPI devuelve 200 OK si la sesión existe en Redis
    if response and response.status == 200 then
        txn.set_var(txn, "txn.authenticated", true)

        local user = string.match(response.body, '"user":"(.-)"')
        if user then
            txn.set_var(txn, "txn.user", user)
        end
    else
        txn.set_var(txn, "txn.authenticated", false)

        if not response then
            core.log(core.err, "Error de conexión: mi_auth_service no responde")
        end
    end
end)
