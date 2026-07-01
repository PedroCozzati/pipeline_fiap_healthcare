export const environment = {
  production: true,
  /** Vazio = mesma origem. Os services já prefixam cada chamada com "/api/...",
   *  e o Nginx faz o proxy de /api/* para o gateway (Cloud Run) ou http://gateway:8000/* (Docker). */
  apiBaseUrl: '',
};
