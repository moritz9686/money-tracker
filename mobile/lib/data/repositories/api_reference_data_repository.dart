import '../../core/networking/api_client.dart';
import '../../domain/models/financial_models.dart';
import '../../domain/repositories/repositories.dart';

class ApiReferenceDataRepository implements ReferenceDataRepository {
  ApiReferenceDataRepository(this._client);

  final ApiClient _client;

  @override
  Future<List<FinancialAccount>> getAccounts() async {
    final response = await _client.getValue('/accounts');
    if (response is! List) throw const ApiException('Unexpected API response');
    return response.map((value) {
      if (value is! Map<String, dynamic>) {
        throw const ApiException('Unexpected API response');
      }
      final currency = value['currency'];
      final name = value['display_name'];
      final id = value['id'];
      if (currency is! String || name is! String || id is! String) {
        throw const ApiException('Unexpected API response');
      }
      return FinancialAccount(
        id: id,
        name: name,
        last4: (value['account_last4'] as String?) ?? '----',
        balance: Money.fromMinorUnits(0, currency),
      );
    }).toList(growable: false);
  }

  @override
  Future<List<Category>> getCategories() async {
    final response = await _client.getValue('/categories');
    if (response is! List) throw const ApiException('Unexpected API response');
    return response.map((value) {
      if (value is! Map<String, dynamic>) {
        throw const ApiException('Unexpected API response');
      }
      final id = value['id'];
      final name = value['name'];
      if (id is! String || name is! String) {
        throw const ApiException('Unexpected API response');
      }
      return Category(id: id, name: name, icon: categoryIcon(name));
    }).toList(growable: false);
  }
}
