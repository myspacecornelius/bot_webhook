import { useState, useEffect } from 'react'
import { 
  Users, 
  Plus,
  Trash2,
  Edit,
  CreditCard,
  MapPin,
  Mail,
  Phone,
  Check,
  X,
  Copy,
  Eye,
  EyeOff
} from 'lucide-react'
import { api } from '../api/client'
import { cn } from '../lib/utils'

interface Profile {
  id: string
  name: string
  email: string
  phone: string
  shippingFirstName: string
  shippingLastName: string
  shippingAddress1: string
  shippingAddress2: string
  shippingCity: string
  shippingState: string
  shippingZip: string
  shippingCountry: string
  cardHolder: string
  cardLast4: string
  cardType: string
}

function ProfileCard({ profile, onEdit, onDelete, onDuplicate }: {
  profile: Profile
  onEdit: () => void
  onDelete: () => void
  onDuplicate: () => void
}) {
  return (
    <div className="bg-[#0f0f18] border border-[#1a1a2e] rounded-xl p-5 hover:border-purple-500/30 transition-all">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center">
            <span className="text-lg font-bold text-white">
              {profile.name.charAt(0).toUpperCase()}
            </span>
          </div>
          <div>
            <h3 className="font-semibold text-white">{profile.name}</h3>
            <p className="text-sm text-gray-500">{profile.email}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-1">
          <button onClick={onDuplicate} className="p-2 text-gray-400 hover:text-white transition-colors" title="Duplicate">
            <Copy className="w-4 h-4" />
          </button>
          <button onClick={onEdit} className="p-2 text-gray-400 hover:text-white transition-colors" title="Edit">
            <Edit className="w-4 h-4" />
          </button>
          <button onClick={onDelete} className="p-2 text-gray-400 hover:text-red-400 transition-colors" title="Delete">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      <div className="space-y-3">
        {/* Shipping */}
        <div className="flex items-start gap-3 p-3 rounded-lg bg-[#1a1a24]">
          <MapPin className="w-4 h-4 text-purple-400 mt-0.5" />
          <div className="text-sm">
            <p className="text-white">{profile.shippingFirstName} {profile.shippingLastName}</p>
            <p className="text-gray-500">{profile.shippingAddress1}</p>
            <p className="text-gray-500">{profile.shippingCity}, {profile.shippingState} {profile.shippingZip}</p>
          </div>
        </div>
        
        {/* Payment */}
        <div className="flex items-center gap-3 p-3 rounded-lg bg-[#1a1a24]">
          <CreditCard className="w-4 h-4 text-green-400" />
          <div className="text-sm">
            <p className="text-white">{profile.cardHolder}</p>
            <p className="text-gray-500">•••• •••• •••• {profile.cardLast4}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function ProfileModal({ profile, onClose, onSaved }: { 
  profile?: Profile | null
  onClose: () => void
  onSaved: () => void 
}) {
  const [showCard, setShowCard] = useState(false)
  const [formData, setFormData] = useState({
    name: profile?.name || '',
    email: profile?.email || '',
    phone: profile?.phone || '',
    shippingFirstName: profile?.shippingFirstName || '',
    shippingLastName: profile?.shippingLastName || '',
    shippingAddress1: profile?.shippingAddress1 || '',
    shippingAddress2: profile?.shippingAddress2 || '',
    shippingCity: profile?.shippingCity || '',
    shippingState: profile?.shippingState || '',
    shippingZip: profile?.shippingZip || '',
    shippingCountry: profile?.shippingCountry || 'United States',
    billingSameAsShipping: true,
    cardHolder: profile?.cardHolder || '',
    cardNumber: '',
    cardExpiry: '',
    cardCvv: '',
  })
  const [loading, setLoading] = useState(false)
  
  const handleSubmit = async () => {
    setLoading(true)
    try {
      await api.createProfile({
        name: formData.name,
        email: formData.email,
        phone: formData.phone,
        shipping_first_name: formData.shippingFirstName,
        shipping_last_name: formData.shippingLastName,
        shipping_address1: formData.shippingAddress1,
        shipping_address2: formData.shippingAddress2,
        shipping_city: formData.shippingCity,
        shipping_state: formData.shippingState,
        shipping_zip: formData.shippingZip,
        shipping_country: formData.shippingCountry,
        billing_same_as_shipping: formData.billingSameAsShipping,
        card_holder: formData.cardHolder,
        card_number: formData.cardNumber,
        card_expiry: formData.cardExpiry,
        card_cvv: formData.cardCvv,
      })
      onSaved()
      onClose()
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }
  
  const states = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
  
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 overflow-y-auto py-10" onClick={onClose}>
      <div className="w-full max-w-2xl bg-[#0f0f18] border border-[#1a1a2e] rounded-2xl p-6 m-4" onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-white mb-6">
          {profile ? 'Edit Profile' : 'Create Profile'}
        </h2>
        
        <div className="space-y-6">
          {/* Profile Info */}
          <div>
            <h3 className="text-sm font-medium text-purple-400 mb-3 flex items-center gap-2">
              <Users className="w-4 h-4" /> Profile Info
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                  placeholder="Profile Name"
                />
              </div>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                placeholder="Email"
              />
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                placeholder="Phone"
              />
            </div>
          </div>
          
          {/* Shipping */}
          <div>
            <h3 className="text-sm font-medium text-purple-400 mb-3 flex items-center gap-2">
              <MapPin className="w-4 h-4" /> Shipping Address
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                value={formData.shippingFirstName}
                onChange={(e) => setFormData({ ...formData, shippingFirstName: e.target.value })}
                className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                placeholder="First Name"
              />
              <input
                type="text"
                value={formData.shippingLastName}
                onChange={(e) => setFormData({ ...formData, shippingLastName: e.target.value })}
                className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                placeholder="Last Name"
              />
              <div className="col-span-2">
                <input
                  type="text"
                  value={formData.shippingAddress1}
                  onChange={(e) => setFormData({ ...formData, shippingAddress1: e.target.value })}
                  className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                  placeholder="Address Line 1"
                />
              </div>
              <div className="col-span-2">
                <input
                  type="text"
                  value={formData.shippingAddress2}
                  onChange={(e) => setFormData({ ...formData, shippingAddress2: e.target.value })}
                  className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                  placeholder="Address Line 2 (optional)"
                />
              </div>
              <input
                type="text"
                value={formData.shippingCity}
                onChange={(e) => setFormData({ ...formData, shippingCity: e.target.value })}
                className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                placeholder="City"
              />
              <div className="grid grid-cols-2 gap-4">
                <select
                  value={formData.shippingState}
                  onChange={(e) => setFormData({ ...formData, shippingState: e.target.value })}
                  className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white focus:outline-none focus:border-purple-500"
                  aria-label="State"
                >
                  <option value="">State</option>
                  {states.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
                <input
                  type="text"
                  value={formData.shippingZip}
                  onChange={(e) => setFormData({ ...formData, shippingZip: e.target.value })}
                  className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                  placeholder="ZIP"
                />
              </div>
            </div>
          </div>
          
          {/* Payment */}
          <div>
            <h3 className="text-sm font-medium text-purple-400 mb-3 flex items-center gap-2">
              <CreditCard className="w-4 h-4" /> Payment Information
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <input
                  type="text"
                  value={formData.cardHolder}
                  onChange={(e) => setFormData({ ...formData, cardHolder: e.target.value })}
                  className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                  placeholder="Cardholder Name"
                />
              </div>
              <div className="col-span-2 relative">
                <input
                  type={showCard ? "text" : "password"}
                  value={formData.cardNumber}
                  onChange={(e) => setFormData({ ...formData, cardNumber: e.target.value.replace(/\D/g, '').slice(0, 16) })}
                  className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 pr-10"
                  placeholder="Card Number"
                />
                <button
                  type="button"
                  onClick={() => setShowCard(!showCard)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                >
                  {showCard ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <input
                type="text"
                value={formData.cardExpiry}
                onChange={(e) => {
                  let v = e.target.value.replace(/\D/g, '').slice(0, 4)
                  if (v.length >= 2) v = v.slice(0, 2) + '/' + v.slice(2)
                  setFormData({ ...formData, cardExpiry: v })
                }}
                className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                placeholder="MM/YY"
              />
              <input
                type="password"
                value={formData.cardCvv}
                onChange={(e) => setFormData({ ...formData, cardCvv: e.target.value.replace(/\D/g, '').slice(0, 4) })}
                className="w-full px-4 py-2.5 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                placeholder="CVV"
              />
            </div>
          </div>
        </div>
        
        <div className="flex justify-end gap-3 mt-6">
          <button onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !formData.name || !formData.email}
            className="flex items-center gap-2 px-5 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
          >
            <Check className="w-4 h-4" />
            {profile ? 'Save Changes' : 'Create Profile'}
          </button>
        </div>
      </div>
    </div>
  )
}

export function Profiles() {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editProfile, setEditProfile] = useState<Profile | null>(null)
  
  const fetchProfiles = async () => {
    try {
      const data = await api.getProfiles()
      setProfiles(data.profiles || [])
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }
  
  useEffect(() => {
    fetchProfiles()
  }, [])
  
  const handleDelete = async (id: string) => {
    if (!confirm('Delete this profile?')) return
    try {
      await api.deleteProfile(id)
      fetchProfiles()
    } catch (e) {
      console.error(e)
    }
  }
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Users className="w-7 h-7 text-purple-400" />
            Profiles
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            {profiles.length} profiles saved
          </p>
        </div>
        
        <button
          onClick={() => { setEditProfile(null); setShowModal(true); }}
          className="flex items-center gap-2 px-5 py-2 bg-purple-600 hover:bg-purple-500 text-white font-medium rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Profile
        </button>
      </div>
      
      {/* Profiles Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : profiles.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-gray-500">
          <Users className="w-16 h-16 mb-4 opacity-30" />
          <p className="text-lg font-medium">No profiles yet</p>
          <p className="text-sm mb-4">Add a profile to use for checkouts</p>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-medium rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Your First Profile
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {profiles.map(profile => (
            <ProfileCard
              key={profile.id}
              profile={profile}
              onEdit={() => { setEditProfile(profile); setShowModal(true); }}
              onDelete={() => handleDelete(profile.id)}
              onDuplicate={() => {/* TODO */}}
            />
          ))}
        </div>
      )}
      
      {/* Modal */}
      {showModal && (
        <ProfileModal
          profile={editProfile}
          onClose={() => setShowModal(false)}
          onSaved={fetchProfiles}
        />
      )}
    </div>
  )
}
