let client, config;

export async function initializeAuth() {
  config = await (await fetch("/api/auth/config")).json();
  if (config.mode !== "entra") return;
  if (!config.client_id || !config.tenant || !config.scope)
    throw new Error("Entra application configuration is incomplete.");
  client = new window.msal.PublicClientApplication({
    auth: {
      clientId: config.client_id,
      authority: `https://login.microsoftonline.com/${config.tenant}`,
      redirectUri: location.origin + "/",
    },
    cache: { cacheLocation: "sessionStorage" },
  });
  await client.initialize();
  const result = await client.handleRedirectPromise();
  if (result?.account) client.setActiveAccount(result.account);
  else if (client.getAllAccounts().length === 1)
    client.setActiveAccount(client.getAllAccounts()[0]);
}

export async function authorization() {
  if (!client?.getActiveAccount()) return {};
  try {
    const result = await client.acquireTokenSilent({
      scopes: [config.scope],
      account: client.getActiveAccount(),
    });
    return { Authorization: `Bearer ${result.accessToken}` };
  } catch {
    throw new Error(
      "Microsoft sign-in needs to be refreshed. Reload and sign in again.",
    );
  }
}

export async function signInMicrosoft() {
  await client.loginRedirect({ scopes: [config.scope] });
}

export async function signOutMicrosoft() {
  await client.logoutRedirect({ postLogoutRedirectUri: location.origin + "/" });
}
