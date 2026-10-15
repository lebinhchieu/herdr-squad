// Every contract fixture; the tests run on all of them. Add a file here when you add a fixture.
import contract_provisional_empty from './contract-provisional-empty'
import contract_provisional_mixed from './contract-provisional-mixed'

export const FIXTURES: Record<string, string> = {
  'contract-provisional-empty': contract_provisional_empty,
  'contract-provisional-mixed': contract_provisional_mixed,
}
