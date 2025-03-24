// Demo data for testing the Hinge-style match UI
export const SAMPLE_MATCHES = {
  success: true,
  matches: [
    {
      id: 'match-1',
      match_date: '2023-11-15T14:30:00Z',
      experience: {
        id: 'exp-1',
        experience_type: 'Dining',
        location: 'Tacoria',
        description: 'I want to try the new restaurant on Nassau Street. Their tacos are supposed to be amazing!',
        latitude: 40.3495,
        longitude: -74.6578,
        location_image: 'https://source.unsplash.com/random/800x600/?mexican+restaurant'
      },
      current_user: {
        id: 'user-1',
        name: 'Alex',
        profile_image: 'https://ui-avatars.com/api/?name=Alex&background=orange&color=fff',
        class_year: '2024'
      },
      other_user: {
        id: 'user-2',
        name: 'Jordan',
        profile_image: 'https://ui-avatars.com/api/?name=Jordan&background=orange&color=fff',
        class_year: '2023',
        bio: 'CS major who loves trying new foods around Princeton. Always up for interesting conversations!'
      }
    },
    {
      id: 'match-2',
      match_date: '2023-11-14T10:15:00Z',
      experience: {
        id: 'exp-2',
        experience_type: 'Studying',
        location: 'Firestone Library',
        description: 'Looking for a study buddy for my upcoming exams. The quiet floor at Firestone is my go-to spot.',
        latitude: 40.3497,
        longitude: -74.6573,
        location_image: 'https://source.unsplash.com/random/800x600/?library'
      },
      current_user: {
        id: 'user-1',
        name: 'Alex',
        profile_image: 'https://ui-avatars.com/api/?name=Alex&background=orange&color=fff',
        class_year: '2024'
      },
      other_user: {
        id: 'user-3',
        name: 'Taylor',
        profile_image: 'https://ui-avatars.com/api/?name=Taylor&background=orange&color=fff',
        class_year: '2025',
        bio: 'Psychology major with a minor in Computer Science. I believe in productive study sessions with good coffee!'
      }
    },
    {
      id: 'match-3',
      match_date: '2023-11-12T18:45:00Z',
      experience: {
        id: 'exp-3',
        experience_type: 'Coffee',
        location: 'Small World Coffee',
        description: 'I want to try their seasonal drinks and maybe chat about life beyond Princeton.',
        latitude: 40.3506,
        longitude: -74.6560,
        location_image: 'https://source.unsplash.com/random/800x600/?coffee+shop'
      },
      current_user: {
        id: 'user-1',
        name: 'Alex',
        profile_image: 'https://ui-avatars.com/api/?name=Alex&background=orange&color=fff',
        class_year: '2024'
      },
      other_user: {
        id: 'user-4',
        name: 'Morgan',
        profile_image: 'https://ui-avatars.com/api/?name=Morgan&background=orange&color=fff',
        class_year: '2024',
        bio: 'English major with a passion for poetry and good coffee. Looking to meet new people outside my usual circle.'
      }
    }
  ]
}; 

// Sample experiences data for the Experiences page
export const SAMPLE_EXPERIENCES = [
  {
    id: 'exp-1',
    user_id: '1',
    experience_type: 'Dining',
    location: 'Tacoria',
    description: 'Amazing Mexican restaurant on Nassau Street with the best tacos in Princeton. Great place for casual meetups with friends!',
    latitude: 40.3495,
    longitude: -74.6578,
    location_image: 'https://source.unsplash.com/random/800x600/?mexican+restaurant',
    is_active: true,
    tags: ['Food', 'Mexican', 'Casual', 'Friends'],
    created_at: '2023-10-15T14:30:00Z',
  },
  {
    id: 'exp-2',
    user_id: '1',
    experience_type: 'Studying',
    location: 'Firestone Library',
    description: 'The quiet floor at Firestone is perfect for focused study sessions, especially during finals week. Great atmosphere and resources.',
    latitude: 40.3497,
    longitude: -74.6573,
    location_image: 'https://source.unsplash.com/random/800x600/?library',
    is_active: true,
    tags: ['Academic', 'Quiet', 'Productive'],
    created_at: '2023-10-20T10:15:00Z',
  },
  {
    id: 'exp-3',
    user_id: '1',
    experience_type: 'Coffee',
    location: 'Small World Coffee',
    description: 'Cozy coffee shop with amazing espresso and pastries. The perfect spot for a coffee date or catching up with someone new.',
    latitude: 40.3506,
    longitude: -74.6560,
    location_image: 'https://source.unsplash.com/random/800x600/?coffee+shop',
    is_active: true,
    tags: ['Coffee', 'Cozy', 'Casual', 'Conversation'],
    created_at: '2023-11-05T18:45:00Z',
  },
  {
    id: 'exp-4',
    user_id: '1',
    experience_type: 'Hiking',
    location: 'Institute Woods',
    description: 'Beautiful trails just minutes from campus. Great for nature lovers and a perfect escape from academic stress.',
    latitude: 40.3425,
    longitude: -74.6691,
    location_image: 'https://source.unsplash.com/random/800x600/?forest+trail',
    is_active: true,
    tags: ['Outdoors', 'Nature', 'Exercise', 'Peaceful'],
    created_at: '2023-09-22T09:30:00Z',
  },
  {
    id: 'exp-5',
    user_id: '1',
    experience_type: 'Museum',
    location: 'Princeton University Art Museum',
    description: 'Incredible collection of art from around the world. Free admission makes it a perfect date spot for art enthusiasts.',
    latitude: 40.3468,
    longitude: -74.6558,
    location_image: 'https://source.unsplash.com/random/800x600/?art+museum',
    is_active: false,
    tags: ['Art', 'Culture', 'Indoor', 'Free'],
    created_at: '2023-11-01T13:20:00Z',
  },
  {
    id: 'exp-6',
    user_id: '1',
    experience_type: 'Concert',
    location: 'Richardson Auditorium',
    description: 'Beautiful venue for classical concerts and performances. The acoustics are phenomenal!',
    latitude: 40.3486,
    longitude: -74.6577,
    location_image: 'https://source.unsplash.com/random/800x600/?concert+hall',
    is_active: true,
    tags: ['Music', 'Culture', 'Evening', 'Formal'],
    created_at: '2023-10-10T19:00:00Z',
  }
]; 