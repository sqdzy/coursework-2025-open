import React, {useState, useEffect} from 'react';

const PLACEHOLDER_BANNER = '/placeholder-banner.png';

const HomepageBanner = ({banner}) => {
    const initialSrc = banner?.image || PLACEHOLDER_BANNER;
    const [imageSrc, setImageSrc] = useState(initialSrc);
    const [hasError, setHasError] = useState(!banner?.image);

    useEffect(() => {
        const newSrc = banner?.image || PLACEHOLDER_BANNER;
        setImageSrc(newSrc);
        setHasError(!banner?.image);
    }, [banner?.image]);

    const handleImageError = () => {
        if (!hasError && imageSrc !== PLACEHOLDER_BANNER) {
            console.warn(`Failed to load banner image: ${banner?.image}. Using placeholder.`);
            setImageSrc(PLACEHOLDER_BANNER);
            setHasError(true);
        }
    };


    if (!banner || !banner.link_url || hasError) {

        return (
            <div
                className="bg-gray-200 aspect-[7/1] md:aspect-[8/1] rounded-lg flex items-center justify-center text-gray-500 mb-8 md:mb-12">

            </div>
        );
    }

    return (
        <a
            href={banner.link_url}
            target="_blank"
            rel="noopener noreferrer"
            className="block w-full overflow-hidden rounded-lg shadow hover:shadow-lg transition-shadow mb-8 md:mb-12"
        >
            <img
                src={imageSrc}
                alt={banner.title || 'Рекламный баннер'}
                className="w-full h-auto object-cover"
                loading="lazy"
                onError={handleImageError}
            />
        </a>
    );
};

export default HomepageBanner;
