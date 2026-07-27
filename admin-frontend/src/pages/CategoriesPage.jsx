import TaxonomyPage from '../components/TaxonomyPage'
import { categoryService } from '../services/catalogService'

export default function CategoriesPage() { return <TaxonomyPage type="category" service={categoryService} /> }
