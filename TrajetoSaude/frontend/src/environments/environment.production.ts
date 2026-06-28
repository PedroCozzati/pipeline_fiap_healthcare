export const environment = {
  production: true,
  /** Em Docker o Nginx faz o proxy de /api/* para http://gateway:8000/* */
  apiBaseUrl: '/api',
};
