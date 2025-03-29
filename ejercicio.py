import google.generativeai as genai

# Configurar la API Key
genai.configure(api_key="AIzaSyAVEtRHU9PcNJt5CWcQ3RIUX55u60KwOvk")

# Crear una función para generar respuestas con Gemini


def get_travel_advice(route_info):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(
        f"El conductor está en {route_info}. ¿Cuál es la mejor ruta para evitar retrasos?")
    return response.text


# Prueba del bot con una ruta de ejemplo
route = "Avenida Central, tráfico denso, destino Terminal Norte"
advice = get_travel_advice(route)
print("Sugerencia para el conductor:", advice)
