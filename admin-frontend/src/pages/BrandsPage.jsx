import TaxonomyPage from '../components/TaxonomyPage'
import { brandService } from '../services/catalogService'

export default function BrandsPage() { return <TaxonomyPage type="brand" service={brandService} /> }
