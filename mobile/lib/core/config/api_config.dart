class ApiConfig {
  const ApiConfig._();

  static const baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  /// Optional development-only request scope for the current backend milestone.
  /// It is not an authentication credential and will be replaced by auth headers.
  static const developmentUserId = String.fromEnvironment(
    'API_DEVELOPMENT_USER_ID',
    defaultValue: '',
  );

  /// Used only by the public browser preview. Production mobile builds use FastAPI.
  static const useMockData = bool.fromEnvironment(
    'USE_MOCK_DATA',
    defaultValue: false,
  );

  static const supabaseUrl = String.fromEnvironment('SUPABASE_URL');
  static const supabasePublishableKey = String.fromEnvironment(
    'SUPABASE_PUBLISHABLE_KEY',
  );
}
